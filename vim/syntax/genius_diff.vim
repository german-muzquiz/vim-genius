" Quit if syntax file is already loaded
if exists("b:current_syntax")
    finish
endif

" Include the standard diff syntax for diff buffers
runtime! syntax/diff.vim

" Highlight the tree header
syntax match geniusTreeHeader /^File Changes:/
highlight default link geniusTreeHeader Title

" Highlight file operations in the list view
syntax match geniusFileAdd /^\s*+ .*/
syntax match geniusFileUpdate /^\s*\~ .*/
syntax match geniusFileDelete /^\s*- .*/

highlight default link geniusFileAdd Green
highlight default link geniusFileUpdate Yellow
highlight default link geniusFileDelete Red

let b:current_syntax = "genius_diff"
