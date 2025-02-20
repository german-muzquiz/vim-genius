" Enable omni completion
setlocal omnifunc=genius#complete_filepath
" Map @ to trigger completion only at the start of a line
inoremap <buffer> <expr> @ col('.') == 1 ? "@\<C-x>\<C-u>" : "@"

