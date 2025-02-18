
" Constants
let s:genius_bufname = 'prompt.genius'
let s:genius_output_bufname = 'output.genius'
let s:default_tag = 'latest'
let s:default_model = 'bedrock:us.anthropic.claude-3-5-sonnet-20241022-v2:0'
let s:is_processing = 0

" Buffer options
let s:buffer_options = {
    \ 'buflisted': 1,
    \ 'buftype': 'nofile',
    \ 'filetype': 'genius',
    \ }

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

    " Set up autocompletion
    setlocal completefunc=genius#complete_filepath

    " Set buffer-local keymap
    nnoremap <buffer> <leader>rf :call <SID>execute_buffer()<CR>
endfunction


function! s:setup_buffer_settings(buf) abort
    call setbufvar(a:buf, '&wrap', 0)
    call setbufvar(a:buf, '&number', 1)
    call setbufvar(a:buf, '&cursorline', 1)
endfunction
 

" Execute the buffer content using the LLM
function! s:execute_buffer() abort
    " Get buffer content
    let l:content = join(getline(1, '$'), "\n")

    " Create temporary file
    let l:tmpfile = tempname()
    call writefile(split(l:content, "\n"), l:tmpfile)

    let l:tag = "latest"
    let l:model = "bedrock:us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    " Common enviornment variables
    let l:env = ' -e OPENAI_API_KEY -e ANTHROPIC_KEY -e AWS_PROFILE -e AWS_REGION  -e BRAVE_API_KEY '
    " Volume dirs
    let l:volumes = ' -v $HOME/.aws:/root/.aws -v $PWD:/context '
    let l:cmd = "/bin/sh -c \"docker run " . l:env . " " . l:volumes . " ghcr.io/german-muzquiz/vim-genius:" . l:tag . " python app/main.py --prompt '" . l:content ."' --model '" . l:model . "'\""
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
    call append(line('$'), split(a:data, "\n"))
    "silent execute 'normal! G'
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

    " Set up autocompletion callback for directories
    augroup GeniusCompletion
        autocmd!
        autocmd CompleteDone * if v:completed_item.user_data == 'dir' | call timer_start(0, {-> s:trigger_completion_after_dir()}) | endif
    augroup END

    return files
endfunction
