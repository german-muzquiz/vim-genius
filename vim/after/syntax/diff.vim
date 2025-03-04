" Enhanced diff syntax highlighting for Genius output

" Load the standard diff syntax
if !exists('b:did_genius_diff_syntax')
  let b:did_genius_diff_syntax = 1
  
  " Only define these if they don't exist yet
  if !hlexists('diffAdded')
    " Define more specific syntax matches for diff content
    syntax match diffAdded "^+.*" contained
    syntax match diffRemoved "^-.*" contained
    syntax match diffLine "^ .*" contained
    syntax match diffIndexLine "^@@ .*" contained
    syntax match diffFile "^--- .*" contained
    syntax match diffNewFile "^+++ .*" contained
    
    " Link to appropriate highlighting groups with stronger settings
    highlight diffAdded ctermfg=Green guifg=Green
    highlight diffRemoved ctermfg=Red guifg=Red
    highlight diffLine ctermfg=Gray guifg=Gray
    highlight diffIndexLine ctermfg=Cyan guifg=Cyan
    highlight diffFile ctermfg=Yellow guifg=Yellow
    highlight diffNewFile ctermfg=Yellow guifg=Yellow
  endif

  " Make sure these are linked to standard diff highlighting groups
  highlight default link diffAdded DiffAdd
  highlight default link diffRemoved DiffDelete
  highlight default link diffLine Normal
  highlight default link diffIndexLine Special
  highlight default link diffFile Type
  highlight default link diffNewFile Type
endif

let b:current_syntax = "diff"

