"-----------------------------------------------------------
" Plugin to execute LLM code generation.
"-----------------------------------------------------------

if exists('g:loaded_vim_genius')
  finish
endif
let g:loaded_vim_genius = 1
let g:markdown_fenced_languages = ['html', 'python', 'bash=sh', 'diff', 'json', 'vim']

command! -nargs=0 Genius call genius#open_genius_buffer()

" Set up status line
set statusline+=%{genius#status()}
