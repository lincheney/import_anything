if __name__ == '__main__':
    from . import import_haml
    from . import main_haml
    
    haml = main_haml.render(
        a_string_passed_into_render = 'which will be rendered',
        another_var = 'Which can be used for dynamic content',
        list_variable = ['list', 'of', 'text'],
    )
    print(haml)
