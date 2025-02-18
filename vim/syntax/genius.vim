" Quit if syntax file is already loaded
if exists("b:current_syntax")
    finish
endif
syntax match filePathReference /^@.*/ 
" Load Python syntax first
syntax include @Python syntax/python.vim
syntax include @Vim syntax/vim.vim
syntax include @Json syntax/json.vim
syntax include @Html syntax/html.vim
" Markdown syntax
syntax match markdownH1 /^# .*/
syntax match markdownH2 /^## .*/
syntax match markdownH3 /^### .*/
syntax match markdownH4 /^#### .*/
syntax match markdownH5 /^##### .*/
syntax match markdownH6 /^###### .*/
syntax match markdownListItem /^\s*[-*+]\s\+/
syntax match markdownNumberedList /^\s*\d\+\.\s\+/
syntax match markdownBold /\*\*[^*]\+\*\*/
syntax match markdownItalic /\*[^*]\+\*/
syntax match markdownLink /\[.\{-}\](\([^)]\+\))/
syntax match markdownCode /`[^`]\+`/
" Special code blocks
syntax region markdownPythonBlock matchgroup=markdownCodeDelimiter start=/^```python\s*$/ end=/^```\s*$/ keepend contains=@Python
syntax region markdownVimBlock matchgroup=markdownCodeDelimiter start=/^```vim\s*$/ end=/^```\s*$/ keepend contains=@Vim
syntax region markdownJsonBlock matchgroup=markdownCodeDelimiter start=/^```json\s*$/ end=/^```\s*$/ keepend contains=@Json
syntax region markdownHtmlBlock matchgroup=markdownCodeDelimiter start=/^```html\s*$/ end=/^```\s*$/ keepend contains=@Html
" Highlight groups
highlight default link markdownH1 Title
highlight default link markdownH2 Title
highlight default link markdownH3 Title
highlight default link markdownH4 Title
highlight default link markdownH5 Title
highlight default link markdownH6 Title
highlight default link markdownListItem Statement
highlight default link markdownNumberedList Statement
highlight default link markdownBold Special
highlight default link markdownItalic Special
highlight default link markdownLink Underlined
highlight default link markdownCode String
highlight default link markdownCodeDelimiter Comment
highlight default link filePathReference Identifier
let b:current_syntax = "genius"

