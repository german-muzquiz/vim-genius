" Quit if syntax file is already loaded
if exists("b:current_syntax")
    finish
endif

" Load markdown syntax as base
runtime! syntax/markdown.vim

" Highlight token usage section
syntax region geniusInfo start=/^-\{80}$/ end=/^-\{80}$/
highlight default link geniusInfo Comment

" Highlight thinking tags
syntax region thinking start="<thinking>" end="</thinking>" contains=@Spell
highlight default link thinking Comment

" Define regions for code_block with operation="add" and different filetypes
syntax region CodeBlockPython matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"python\".*operation=\"add\".*>" end="</code_block>" contains=@Python keepend
syntax region CodeBlockJavaScript matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"javascript\".*operation=\"add\".*>" end="</code_block>" contains=@JavaScript keepend
syntax region CodeBlockHTML matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"html\".*operation=\"add\".*>" end="</code_block>" contains=@HTML keepend
syntax region CodeBlockCSS matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"css\".*operation=\"add\".*>" end="</code_block>" contains=@CSS keepend
syntax region CodeBlockJSON matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"json\".*operation=\"add\".*>" end="</code_block>" contains=@JSON keepend
syntax region CodeBlockVim matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"vim\".*operation=\"add\".*>" end="</code_block>" contains=@VIM keepend
syntax region CodeBlockShell matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"sh\".*operation=\"add\".*>" end="</code_block>" contains=@Shell keepend
syntax region CodeBlockRuby matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"ruby\".*operation=\"add\".*>" end="</code_block>" contains=@Ruby keepend
syntax region CodeBlockYAML matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"yaml\".*operation=\"add\".*>" end="</code_block>" contains=@YAML keepend
syntax region CodeBlockC matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"c\".*operation=\"add\".*>" end="</code_block>" contains=@C keepend
syntax region CodeBlockCPP matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"cpp\".*operation=\"add\".*>" end="</code_block>" contains=@CPP keepend
syntax region CodeBlockJava matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"java\".*operation=\"add\".*>" end="</code_block>" contains=@Java keepend
syntax region CodeBlockGo matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"go\".*operation=\"add\".*>" end="</code_block>" contains=@Go keepend
syntax region CodeBlockRust matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"rust\".*operation=\"add\".*>" end="</code_block>" contains=@Rust keepend
syntax region CodeBlockSQL matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"sql\".*operation=\"add\".*>" end="</code_block>" contains=@SQL keepend
syntax region CodeBlockText matchgroup=CodeBlockDelimiter start="<code_block.*filetype=\"txt\".*operation=\"add\".*>" end="</code_block>" contains=@Text keepend

" Define regions for code_block with operation="update" - always use diff syntax
syntax include @Diff syntax/diff.vim
syntax region diffRegion start=/^---/ end=/^\s*$/ contains=diffFile,diffNewFile,diffIndexLine,diffLine,diffSubname,diffComment,diffLine,diffAdded,diffRemoved,diffChanged contained
syntax region CodeBlockUpdate matchgroup=CodeBlockDelimiter start="<code_block.*operation=\"update\".*>" end="</code_block>" contains=diffRegion,@Diff keepend

" Define regions for code_block with operation="delete"
syntax region CodeBlockDelete matchgroup=CodeBlockDelimiter start="<code_block.*operation=\"delete\".*>" end="</code_block>" keepend
highlight default link CodeBlockDelete Comment

" Default for any other filetype
syntax region CodeBlockGeneric matchgroup=CodeBlockDelimiter start="<code_block.*operation=\"add\".*>" end="</code_block>" keepend

highlight default link CodeBlockDelimiter Special
let b:current_syntax = "genius_output"

