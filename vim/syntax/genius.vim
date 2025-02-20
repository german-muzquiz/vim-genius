" Quit if syntax file is already loaded
if exists("b:current_syntax")
    finish
endif
runtime syntax/markdown.vim
syntax match filePathReference /^@.*/ 
highlight default link filePathReference Identifier
let b:current_syntax = "genius"

