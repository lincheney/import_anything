if __name__ == '__main__':
    from . import import_haml
    from . import main_haml
    
    haml = main_haml.render(
        title = 'MyPage',
        item = dict(type = 'massive', number = 4, urgency = 'urgent'),
        sortcol = None,
        sortdir = '/tmp',
        href = '/index.html#more-stuff',
        link = dict(href = '#'),
        article = dict(number = 27, visibility = 'visible'),
        link_to_remote = lambda *a, **kwa: None,
        product = dict(id = 3),
    )
    print(haml)
