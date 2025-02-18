# vim-genius

AI code assistant for Vim.

## Overview

vim-genius is a vim plugin that executes a companion docker container to generate code suggestions from the given prompt and context files.
The docker container is a python CLI tool that uses pydanticai packed wit different tools.

### Interface between the vim plugin and docker

The vim plugin executes a command similar to this:
```sh
docker run --rm -v ${PWD}:/repo -it vim-genius:latest python -m vim_genius "$@"
```


