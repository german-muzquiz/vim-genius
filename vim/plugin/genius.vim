"-----------------------------------------------------------
" Plugin to execute LLM code generation.
"-----------------------------------------------------------

if exists('g:loaded_vim_genius')
  finish
endif
let g:loaded_vim_genius = 1
let g:markdown_fenced_languages = ['html', 'python', 'bash=sh', 'diff', 'json', 'vim']
let g:genius_statusline_icon = get(g:, 'genius_statusline_icon', '🤖')

command! -nargs=0 Genius call genius#open_genius_buffer()
command! -nargs=0 GeniusConfig call genius#open_config()
command! -nargs=0 GeniusHistory call genius#show_history()
command! -nargs=0 GeniusToggleOutput call genius#toggle_output()

" Set up status line
set statusline+=%{genius#status()}
