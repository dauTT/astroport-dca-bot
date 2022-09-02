def row_string(table_object) -> str:
    _repr = ["{} = {}".format(k, table_object.__dict__[k])
             for k in table_object.__dict__.keys() if k != "_sa_instance_state"]
    nice_string = """
    """.join(_repr)
    return """[
    {}
]""".format(nice_string)
