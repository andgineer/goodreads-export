from goodreads_export.templates import DEFAULT_BUILTIN_TEMPLATE, TemplatesLoader


def test_templates_load_embeded():
    templates = TemplatesLoader().load_builtin(builtin_name=DEFAULT_BUILTIN_TEMPLATE)
    assert templates.series and templates.book and templates.author and templates.name
