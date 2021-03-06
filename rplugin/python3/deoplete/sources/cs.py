import re
import json
import urllib
import urllib.request
import urllib.parse
from .base import Base


class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'cs'
        self.mark = '[CS]'
        self.rank = 1000
        self.filetypes = ['cs']
        self.input_pattern = '\.\w*'
        self.is_bytepos = True

    def on_init(self, context):
        host = self.vim.eval("get(g:, 'OmniSharp_host')")
        if host:
            self.__url = "{}/autocomplete".format(host)
        else:
            self.__url = None

    def get_complete_position(self, context):
        m = re.search(r'\w*$', context['input'])
        return m.start() if m else -1

    def gather_candidates(self, context):
        if self.__url is None:
            return []

        cur = self.vim.current
        win = cur.window
        cursor = win.cursor
        buf = cur.buffer
        lines = [str(i) for i in buf[:]]

        params = {
            'line': str(cursor[0]),
            'column': str(cursor[1]+1),
            'buffer': '\n'.join(lines),
            'filename': str(cur.buffer.name),
            'wordToComplete': context['complete_str'],
            'WantMethodHeader': True,
            'WantReturnType': True,
            'WantDocumentationForEveryCompletionResult': True
        }
        data = bytes(json.dumps(params), 'utf-8')

        req = urllib.request.Request(
            self.__url, data, headers={'Content-Type': 'application/json; charset=UTF-8'},
            method='POST')
        try:
            with urllib.request.urlopen(req) as f:
                r = str(f.read(), 'utf-8')
        except Exception as ex:
            r = None
            self.vim.command('echomsg "{}"'.format(ex))

        if r is None or len(r) == 0:
            return []
        l = json.loads(r)
        if l is None:
            return []

        completions = []
        for item in l:
            display = item['MethodHeader'] if item['MethodHeader'] is not None and len(item['MethodHeader']) > 0 else item['CompletionText']
            display += '\t'
            display += item['ReturnType'] if item['ReturnType'] is not None and len(item['ReturnType']) > 0 else item['DisplayText']

            completionText = item['CompletionText']
            description = item['Description'].replace('\r\n', '\n') if item['Description'] is not None else ''

            completions.append(dict(
                word=completionText,
                abbr=display,
                info=description,
                icase=1,
                dup=1))

        return completions
