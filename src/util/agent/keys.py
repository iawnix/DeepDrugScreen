from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

# 自定义快捷键绑定
CLI_KEY = KeyBindings()
@CLI_KEY.add(Keys.Enter)
def submit(event):
    event.current_buffer.validate_and_handle()
@CLI_KEY.add(Keys.ControlBackslash)
def newline(event):
    event.current_buffer.insert_text('\n')


