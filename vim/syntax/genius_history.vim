" Quit if syntax file is already loaded
if exists("b:current_syntax")
    finish
endif

" Highlight the history header
syntax match geniusHistoryHeader /^# Genius.*/
highlight default link geniusHistoryHeader Title

" Highlight history entries
syntax match geniusHistoryEntry /^\d\+\. .*/
highlight default link geniusHistoryEntry Identifier

let b:current_syntax = "genius_history"

