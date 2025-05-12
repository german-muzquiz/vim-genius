# TASKS

This file outlines the steps required to implement the new `:GeniusInit` Vim command, which will launch the assistant with the `INIT_PROJECT_PROMPT`.

## 1. Extend the Python CLI

- Open `genius_assistant/main.py`.
- Add a new CLI flag/argument (e.g. `--init` or `--prompt init`).
- When this flag is provided, import `INIT_PROJECT_PROMPT` from `genius_assistant/prompts.py` and pass it to the agent runner instead of the default prompt.

## 2. Expose `INIT_PROJECT_PROMPT`

- Verify that `genius_assistant/prompts.py` exports `INIT_PROJECT_PROMPT`.
- If it does not, add a constant or function that returns the special initialization prompt.

## 3. Add the Vim Command

- In `vim/plugin/genius.vim` (or the appropriate plugin file), define:

  ```vim
  command! GeniusInit call genius#run('--init')
  ```

- Adjust `genius#run()` or whatever entrypoint to accept and forward the `--init` flag to the Python script.

## 4. Shell Bridge

- Ensure that the Vim autoload or plugin layer invokes the external `main.py` script with the correct parameters.
- Example invocation:

  ```vim
  execute 'silent !python3 ' . s:script_path . ' --init'
  ```

- Make sure the path resolution to `genius_assistant/main.py` is robust.

## 5. Update Documentation

- Add a section in `README.md` (and `vim/doc/genius.txt`) describing the new `:GeniusInit` command.
- Show usage examples.

