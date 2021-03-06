import re

def _re_var_escape(s):
    return re.sub(r'([\.\*\\\+\^\$\(\)\[\]\|\{\}\?])', '\\\\\\1', s)

def re_replacer(variables):
    res = {}
    for k, v in variables.items():
        res['\\{\\{ *%s *\\}\\}' % _re_var_escape(str(k))] = _re_var_escape(str(v))
    return res

def default(html: str, *args, **kwargs) -> str:
    replacer = {**dict(((i, args[i] for i in range(len(args))))), **kwargs}
    for pattern, dest in re_replacer(replacer).items():
        html = re.sub(pattern, dest, html)
    return html
