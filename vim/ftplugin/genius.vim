" Enable omni completion
setlocal omnifunc=genius#complete_filepath
"
" Set up folding for code blocks
setlocal foldmethod=marker
setlocal foldmarker=<code_block,</code_block>
setlocal foldenable
setlocal foldlevel=0

" Map @ to trigger completion only at the start of a line
inoremap <buffer> <expr> @ col('.') == 1 ? "@\<C-x>\<C-u>" : "@"

" Map <leader>r to execute the buffer
nnoremap <buffer> <leader>r :call genius#display_file_diff()<CR>
