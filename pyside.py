from SCons.Script import Builder


def generate(env):
    env.Append(BUILDERS={
        'PySideUI': Builder(action='$PYSIDE_UIC $SOURCE > $TARGET',
                            src_suffix='.ui', suffix='.py',
                            single_source=True)
    })
    env.SetDefault(PYSIDE_UIC='pyside-uic')


def exists(env):
    return True
