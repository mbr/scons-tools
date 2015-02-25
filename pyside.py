from SCons.Script import Builder


def generate(env):
    env.Append(BUILDERS={
        'PySideUI': Builder(action='$PYSIDE_UIC $SOURCE > $TARGET',
                            src_suffix='.ui', suffix='.py',
                            single_source=True),
        'PySideUIMerge': Builder(action='$PYSIDE_UIMERGE $SOURCES > $TARGET'),
        'PySideRC': Builder(action='$PYSIDE_RCC $SOURCE > $TARGET',
                            src_suffix='.qrc', suffix='.py',
                            single_source=True)
    })
    env.SetDefault(PYSIDE_UIC='pyside-uic')
    env.SetDefault(PYSIDE_RCC='pyside-rcc')
    env.SetDefault(PYSIDE_UIMERGE='cat')


def exists(env):
    return True
