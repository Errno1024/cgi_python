import cgi
import sys as _sys
import types as _types
import _io

PY2 = _sys.version_info[0] == 2
PY3 = _sys.version_info[0] == 3
PY34 = _sys.version_info[0:2] >= (3, 4)

# The following code is from six

if PY3:
    string_types = (str,)
    integer_types = (int,)
    class_types = (type,)
    text_type = str
    binary_type = bytes

    MAXSIZE = _sys.maxsize
else:
    string_types = (basestring,)
    integer_types = (int, long)
    class_types = (type, _types.ClassType)
    text_type = unicode
    binary_type = str

    if _sys.platform.startswith("java"):
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):
            def __len__(self):
                return 1 << 31

        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
        del X

def _ensure_text(s, encoding="utf-8", errors="strict"):
    """Coerce *s* to six.text_type.

    For Python 2:
      - `unicode` -> `unicode`
      - `str` -> `unicode`

    For Python 3:
      - `str` -> `str`
      - `bytes` -> decoded to `str`
    """
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    elif isinstance(s, text_type):
        return s
    else:
        raise TypeError("not expecting type '%s'" % type(s))


from . import engines

def url_escape(url: str) -> str:
    ESCAPE = [
        (' ', '%20'),
        ('"', '%22'),
        ('#', '%23'),
        ('%', '%25'),
        ('&', '%26'),
        ('(', '%28'),
        (')', '%29'),
        ('+', '%2B'),
        (',', '%2C'),
        ('/', '%2F'),
        (':', '%3A'),
        (';', '%3B'),
        ('<', '%3C'),
        ('=', '%3D'),
        ('>', '%3E'),
        ('?', '%3F'),
        ('@', '%40'),
        ('\\', '%5C'),
        ('|', '%7C'),
    ]
    for k, v in ESCAPE:
        url = url.replace(k, v)
    return url

def form_data(*args, **kwargs) -> cgi.FieldStorage:
    return cgi.FieldStorage(*args, **kwargs)

def error(*values, sep=' ', file=_sys.stderr) -> None:
    print(*values, sep=sep, end='', file=file)

def output(*values, sep='\n', end='\n', file=_sys.stdout) -> None:
    print(*values, sep=sep, end=end, file=file)

def _raise_wrong_type(errtype, obj, type):
    raise errtype(f'expected {type.__name__} object, got \'{obj.__class__.__name__}\'')

def _type_check(obj, type):
    if not isinstance(obj, type):
        _raise_wrong_type(ValueError, obj, type)

_header_map = {
    'Content-type': ('Content_type', ),
    'Last-modified': ('Last_modified', ),
    'Content-length': ('Content_length', ),
    'Set-Cookie': ('Cookies', 'Set_cookie', ),
    'Expires': (),
    'Location': ('Redirect', ),
}

def _headers_prepare(headers):
    return map(lambda x: (str(x[0]).capitalize(), str(x[1])), headers.items())

def set_headers(*headers, cookies: dict=None, file=_sys.stdout, **kwargs):
    hs = {'Content-type': 'text/html'}
    for header in headers:
        _type_check(header, dict)
        hs.update(_headers_prepare(header))
    hs.update(_headers_prepare(kwargs))
    for hname, candidates in _header_map.items():
        found = False
        if hname in hs:
            found = True
        for name in candidates:
            if name in hs:
                if not found:
                    hs[hname] = hs[name]
                    found = True
                hs.pop(name)
    if not 'Cookies' in hs and cookies:
        _type_check(cookies, dict)
        cks = ';'.join(map(lambda x: f'{url_escape(str(x[0]))}={url_escape(str(x[1]))}', cookies.items()))
        hs['Set-Cookie'] = cks
    output(*map(lambda x: f'{x[0]}: {x[1]}', hs.items()), end='\n\n')


class Arguments:
    def __init__(self, *args, **kwargs):
        self.__args__ = list(args)
        self.__kwargs__ = kwargs

    def update(self, *args, **kwargs):
        self.__args__.extend(args)
        self.__kwargs__.update(kwargs)

    def clear(self):
        self.__args__ = []
        self.__kwargs__.clear()

    def get(self, item, default=NotImplemented):
        if isinstance(item, slice):
            return self.__args__[item]
        if isinstance(item, int):
            try:
                return self.__args__[item]
            except: pass
        if default == NotImplemented:
            return self.__kwargs__.get(item)
        return self.__kwargs__.get(item, default)

    def copy(self):
        return self.__class__(*self.__args__, **self.__kwargs__)

    def __len__(self):
        return len(self.__args__) + len(self.__kwargs__)

    def __getitem__(self, item):
        return self.get(item)

    def set(self, key, value):
        if isinstance(key, slice):
            ori = self.__args__[key]
            self.__args__[key] = value
            return ori
        if isinstance(key, int):
            try:
                ori = self.__args__[key]
                self.__args__[key] = value
                return ori
            except: pass
        ori = self.__kwargs__.get(key, None)
        self.__kwargs__[key] = value
        return ori

    def __setitem__(self, key, value):
        self.set(key, value)

    def __str(self):
        args = ', '.join(map(str, self.__args__))
        kwargs = ', '.join(map(lambda x: f'{x[0]}: {x[1]}', self.__kwargs__.items()))
        if self.__args__:
            if self.__kwargs__:
                return args + ', ' + kwargs
            return args
        return kwargs

    def __str__(self):
        return '{%s}' % self.__str()

    def __repr__(self):
        return '%s(%s)' % (self.__name__, self.__str())

    def call(self, func: callable, *args, **kwargs):
        return func(*args, *self.__args__, **kwargs, **self.__kwargs__)


def parse_html(source, arguments: Arguments=None, *args, encoding='utf-8',
                engine: callable=engines.default, **kwargs) -> str:
    if isinstance(arguments, Arguments):
        arguments = arguments.copy()
        if args or kwargs:
            arguments.update(*args, **kwargs)
    elif isinstance(arguments, dict):
        arguments = Arguments(**arguments)
        if args or kwargs:
            arguments.update(*args, **kwargs)
    elif arguments is None:
        arguments = Arguments(*args, **kwargs)
    else:
        arguments = Arguments(arguments, *args, **kwargs)
    if isinstance(source, (binary_type, text_type)):
        html = _ensure_text(source, encoding=encoding)
    elif isinstance(source, _io._IOBase):
        html = _ensure_text(source.read(), encoding=encoding)
    else:
        raise ValueError(f'expected {text_type.__name__} object, {binary_type.__class__} object or file object, '
                         f'got \'{source.__class__.__name__}\'')
    return arguments.call(engine, html)

def output_html(source, arguments: Arguments=None, *args, encoding='utf-8',
                engine: callable=engines.default, **kwargs) -> str:
    res = parse_html(source, arguments, *args, encoding=encoding, engine=engine, **kwargs)
    output(res, end='\n')
    return res
