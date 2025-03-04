" Load syntax files for embedded languages
if !exists('g:loaded_genius_output_syntax')
  let g:loaded_genius_output_syntax = 1
  
  " Include syntax files for various languages
  syn include @Python syntax/python.vim
  syn include @JavaScript syntax/javascript.vim
  syn include @HTML syntax/html.vim
  syn include @CSS syntax/css.vim
  syn include @JSON syntax/json.vim
  syn include @VIM syntax/vim.vim
  syn include @Shell syntax/sh.vim
  syn include @Diff syntax/diff.vim
  
  " Include additional languages if they exist
  silent! syn include @Ruby syntax/ruby.vim
  silent! syn include @YAML syntax/yaml.vim
  silent! syn include @C syntax/c.vim
  silent! syn include @CPP syntax/cpp.vim
  silent! syn include @Java syntax/java.vim
  silent! syn include @Go syntax/go.vim
  silent! syn include @Rust syntax/rust.vim
  silent! syn include @SQL syntax/sql.vim
  silent! syn include @Text syntax/text.vim
  
  " Make sure diff syntax is properly loaded
  syn include @Diff syntax/diff.vim
  
  " Set up diff highlighting for update operations
  hi def link diffAdded DiffAdd
  hi def link diffRemoved DiffDelete
endif

