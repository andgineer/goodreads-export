from goodreads_export.templates import DEFAULT_BUILTIN_TEMPLATE, RegEx, RegExList, TemplatesLoader


def test_templates_load_embeded():
    templates = TemplatesLoader().load_builtin(builtin_name=DEFAULT_BUILTIN_TEMPLATE)
    assert templates.series and templates.book and templates.author and templates.name


def test_multi_regex():
    regex_a = RegEx(regex=r"a")
    regex_b = RegEx(regex=r"b")
    regex_list = RegExList(
        [
            regex_a,
            regex_b,
        ]
    )
    assert regex_a == regex_list.choose_regex("a")
    assert regex_b == regex_list.choose_regex("b")
