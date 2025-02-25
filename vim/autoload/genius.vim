
" Constants
let s:genius_bufname = 'prompt.genius'
let s:genius_output_bufname = 'output.genius'
let s:default_tag = 'latest'
let s:genius_config_file = expand('~/.vim_genius')
"let s:default_model = 'openrouter:anthropic/claude-3.5-sonnet'
"let s:default_model = 'bedrock:us.anthropic.claude-3-5-sonnet-20241022-v2:0'
let s:is_processing = 0

" Buffer options
let s:buffer_options = {
    \ 'buflisted': 1,
    \ 'buftype': 'nofile',
    \ 'filetype': 'genius',
    \ }

" Prompt header
let s:prompt_header = [
    \ '# ----------------------------------------------------------------------',
    \ '# Help',
    \ '# <leader>r - Sends the current prompt to the LLM',
    \ '# <leader>c - Opens the Genius configuration file',
    \ '#',
    \ '# Inject files and folders:',
    \ '# @folder/ - Injects the contents of the folder into the prompt',
    \ '# @file - Injects the contents of the file into the prompt',
    \ '# @https://abc.com - Injects the contents of the URL into the prompt',
    \ '# ----------------------------------------------------------------------',
    \ '',
    \ ]

" Create and setup the genius config file
function! genius#open_config() abort
    " Create config file if it doesn't exist
    if !filereadable(s:genius_config_file)
        let l:default_config = [
            \ '# ---------------------------------------------------------------------',
            \ '# Vim Genius configuration settings',
            \ '# ---------------------------------------------------------------------',
            \ '# API family for the LLM to be used. Must be one of: openai, anthropic, bedrock or openrouter',
            \ 'API_FAMILY=',
            \ '',
            \ '# LLM model name to use as indicated by the API family documentation',
            \ 'MODEL_NAME=',
            \ '',
            \ '# API key for authentication.',
            \ '# If API_FAMILY is set to bedrock this is not required as AWS credentials are read from the environment and $HOME/.aws/credentials and $HOME/.aws/config files',
            \ 'MODEL_API_KEY='
            \ ]
        call writefile(l:default_config, s:genius_config_file)
    endif
    
    " Open config file in a new buffer
    execute 'edit ' . s:genius_config_file
    
    " Set buffer options
    setlocal filetype=sh
endfunction


" Create and setup the genius input buffer
function! genius#open_genius_buffer() abort
    let l:buf = bufadd(s:genius_bufname)
    
    " Set buffer options
    for [key, value] in items(s:buffer_options)
        call setbufvar(l:buf, '&' . key, value)
    endfor
    
    " Set buffer-local settings
    call s:setup_buffer_settings(l:buf)
    
    " Switch to the buffer
    execute 'buffer' l:buf

    " Inject header into buffer
    call setline(1, s:prompt_header)

    " Move to the end of the buffer
    normal! G

    " Set up autocompletion
    setlocal completefunc=genius#complete_filepath

    " Set buffer-local keymap
    nnoremap <buffer> <leader>r :call <SID>execute_buffer()<CR>
    nnoremap <buffer> <leader>c :call genius#open_config()<CR>
endfunction


function! s:setup_buffer_settings(buf) abort
    call setbufvar(a:buf, '&wrap', 0)
    call setbufvar(a:buf, '&number', 1)
    call setbufvar(a:buf, '&cursorline', 1)
endfunction
 

" Execute the buffer content using the LLM
function! s:execute_buffer() abort
    " Get buffer content except header
    let l:content = join(getline(len(s:prompt_header), '$'), "\n")

    " Create temporary file
    let l:tmpfile = tempname()
    call writefile(split(l:content, "\n"), l:tmpfile)

    " Add AWS environment variables only if API_FAMILY is bedrock
    if filereadable(s:genius_config_file) && system('grep "^API_FAMILY=bedrock" ' . s:genius_config_file) != ''
        let l:env = '-e AWS_PROFILE -e AWS_REGION -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN'
        let l:volumes = '-v $HOME/.aws:/root/.aws -v ' . s:genius_config_file . ':/root/.vim_genius -v $PWD:/context'
    else
        let l:env = ''
        let l:volumes = '-v ' . s:genius_config_file . ':/root/.vim_genius -v $PWD:/context'
    endif
    let l:cmd = "/bin/sh -c \"docker run --rm " . l:env . " " . l:volumes . " ghcr.io/german-muzquiz/vim-genius:" . s:default_tag . " python app/main.py --prompt '" . l:content ."'"
    "echom l:cmd

    " Create or get output buffer
    let l:output_buf = bufadd(s:genius_output_bufname)

    " Set output buffer options
    call setbufvar(l:output_buf, '&swapfile', 0)
    call setbufvar(l:output_buf, '&filetype', 'genius')
    call setbufvar(l:output_buf, '&buftype', 'nofile')
    call setbufvar(l:output_buf, '&buflisted', 1)

    " Find if output buffer is already displayed in a window
    let l:output_win = bufwinnr(l:output_buf)
    
    if l:output_win == -1
        " Output buffer is not displayed, create new split
        silent execute 'vertical belowright split'
    else
        " Output buffer is displayed, switch to its window
        execute l:output_win . 'wincmd w'
    endif
    
    " Switch to the output buffer and clear it
    let l:current_win = winnr() 
    execute 'buffer' l:output_buf

    " Clear and set output buffer content
    silent %delete _

    " Set processing flag
    let s:is_processing = 1

    " Start the asynchronous job
    let l:job = job_start(l:cmd, {
            \ 'out_cb': { id, data -> s:on_job_output(id, data, l:output_buf) },
            \ 'err_cb': { id, data -> s:on_job_output(id, data, l:output_buf) },
            \ 'exit_cb': function('s:on_job_exit'),
            \ })

    if job_status(l:job) !=# 'run'
        echom "Failed to start job"
    endif

    " Delete temporary file (if no longer needed)
    call delete(l:tmpfile)
endfunction


" This callback gets called every time new output is received:
function! s:on_job_output(job_id, data, output_buf) abort
    call appendbufline(a:output_buf, '$', a:data)
    redraw
endfunction


" This callback is called when the job finishes.
function! s:on_job_exit(job_id, exit_status) abort
    redraw
    echom "LLM finished with status " . a:exit_status
    let s:is_processing = 0
endfunction


function! genius#status() abort
    return s:is_processing ? '🤖 Processing...' : ''
endfunction


" Helper function to trigger completion after inserting a directory
function! s:trigger_completion_after_dir() abort
    call feedkeys("\<C-x>\<C-u>", 'n')
endfunction


" File path completion function
function! genius#complete_filepath(findstart, base) abort
    if a:findstart
        " Locate the start of the filepath after @
        let line = getline('.')
        let start = col('.') - 1
        while start > 0 && line[start - 1] != '@'
            let start -= 1
        endwhile
        return start
    endif

    " Find matching files
    let files = []
    let path = a:base
    let dir = '.'

    " If base contains a path, use it as directory
    if a:base =~ '/'
        let dir = fnamemodify(a:base, ':h')
        let path = fnamemodify(a:base, ':t')
        let base_path = dir . '/'
    endif

    for item in glob(dir . '/*', 0, 1)
        let item_name = fnamemodify(item, ':t')
        if item_name =~ '^' . path
            let display_name = a:base == '' ? item_name : substitute(item, '^' . dir . '/', '', '')
            let full_word = isdirectory(item) ? display_name . '/' : display_name
            call add(files, {
                \ 'word': full_word,
                \ 'menu': isdirectory(item) ? '[Dir]' : '[File]',
                \ 'dup': 0,
                \ 'user_data': isdirectory(item) ? 'dir' : 'file'
                \ })
        endif
    endfor

    " Prepend base path to all completions if we're in a subdirectory
    if exists('base_path')
        for item in files
            let item.word = base_path . item.word
        endfor
    endif

    " Set up autocompletion callback for directories only if we have a completed item
    if !empty(v:completed_item)
        augroup GeniusCompletion
            autocmd!
            if has_key(v:completed_item, 'user_data')
                if v:completed_item.user_data == 'dir'
                    call timer_start(0, {-> s:trigger_completion_after_dir()})
                endif
            endif
        augroup END
    endif

    return files
endfunction
