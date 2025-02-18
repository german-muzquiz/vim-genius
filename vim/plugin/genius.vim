"-----------------------------------------------------------
" Plugin to execute LLM code generation.
"-----------------------------------------------------------

if exists('g:loaded_vim_genius')
  finish
endif
let g:loaded_vim_genius = 1

command! -nargs=0 Genius call genius#open_genius_buffer()

" Set up status line
set statusline+=%{genius#status()}
