
" Constants
let s:default_tag = 'latest'
let s:genius_config_file = expand('~/.vim_genius')
let s:genius_bufname = 'Genius: Prompt'
let s:genius_output_bufname = 'Genius: Output'
let s:history_dir = expand('~/.vim_genius_history')
let s:max_history_files = 50
let s:genius_history_bufname = 'Genius: History'
let s:is_processing = 0

" Buffer options
let s:buffer_options = {
    \ 'buflisted': 1,
    \ 'buftype': 'nofile',
    \ 'swapfile': 0,
    \ 'filetype': 'genius',
    \ }

" Prompt header
let s:prompt_header = [
    \ '# ----------------------------------------------------------------------',
    \ '# Help',
    \ '# <leader>g - Open Genius prompt buffer',
    \ '# <leader>h - Show prompt history',
    \ '# <leader>r - Sends the current prompt to the LLM',
    \ '# <leader>c - Opens the Genius configuration file',
    \ '#',
    \ '# Inject files and folders:',
    \ '# @folder/ - Injects the contents of the folder into the prompt',
    \ '# @file - Injects the contents of the file into the prompt',
    \ '# @https://abc.com - Injects the contents of the URL into the prompt',
    \ '#',
    \ '# Type @ and press Tab to autocomplete file paths',
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
            \ '# Example: API_FAMILY=openai',
            \ '',
            \ '# LLM model name to use as indicated by the API family documentation',
            \ 'MODEL_NAME=',
            \ '',
            \ '# API key for authentication.',
            \ '# If API_FAMILY is set to bedrock this is not required as AWS credentials are read from the environment and $HOME/.aws/credentials and $HOME/.aws/config files',
            \ 'MODEL_API_KEY='
            \ ]
        " Create directory for history if it doesn't exist
        call mkdir(s:history_dir, "p", 0700)
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
    nnoremap <buffer> <leader>h :call genius#show_history()<CR>
    nnoremap <buffer> <leader>g :call genius#open_genius_buffer()<CR>
    nnoremap <buffer> <leader>c :call genius#open_config()<CR>
endfunction


function! s:setup_buffer_settings(buf) abort
    call setbufvar(a:buf, '&wrap', 0)
    call setbufvar(a:buf, '&number', 1)
    call setbufvar(a:buf, '&cursorline', 1)
endfunction
 

" Toggle buffer in window
function! s:toggle_buffer_window(buf) abort
    let l:win = bufwinnr(a:buf)
    
    if l:win == -1
        " Buffer is not displayed, create new split
        silent execute 'vertical belowright split'
        execute 'buffer' a:buf
    else
        " Buffer is displayed, close its window
        execute l:win . 'wincmd c'
    endif
endfunction


" Save prompt to history
function! s:save_to_history(prompt) abort
    " Create timestamp for filename
    let l:timestamp = strftime('%Y%m%d_%H%M%S')
    let l:filename = s:history_dir . '/' . l:timestamp . '.genius'

    " Create foler if it doesn't exist
    call mkdir(s:history_dir, "p", 0700)
    
    " Write prompt to file
    call writefile(split(a:prompt, "\n"), l:filename)
    
    " Clean up old history files if we have too many
    let l:history_files = sort(glob(s:history_dir . '/*.genius', 0, 1))
    if len(l:history_files) > s:max_history_files
        call delete(l:history_files[0])
    endif
    return l:filename
endfunction

" Execute the buffer content using the LLM
function! s:execute_buffer() abort
    " Get buffer content except header
    let l:content = join(getline(len(s:prompt_header), '$'), "\n")

    " Create temporary file
    " Save prompt to history and create a temporary file for docker to read
    call s:save_to_history(l:content)

    " Create a temporary directory for mounting
    let l:tmp_dir = tempname()
    call mkdir(l:tmp_dir, "p", 0700)
    
    " Create prompt file in the temporary directory
    let l:prompt_file = l:tmp_dir . '/prompt.txt'
    call writefile(split(l:content, "\n"), l:prompt_file)
    
    " Add AWS environment variables only if API_FAMILY is bedrock
    if filereadable(s:genius_config_file) && system('grep "^API_FAMILY=bedrock" ' . s:genius_config_file) != ''
        let l:env = '-e AWS_PROFILE -e AWS_REGION -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN'
        let l:volumes = '-v $HOME/.aws:/root/.aws -v ' . s:genius_config_file . ':/root/.vim_genius -v $PWD:/context -v ' . l:tmp_dir . ':/prompt'
    else
        let l:env = ''
        let l:volumes = '-v ' . s:genius_config_file . ':/root/.vim_genius -v $PWD:/context -v ' . l:tmp_dir . ':/prompt'
    endif
    let l:cmd = "/bin/sh -c \"docker run --rm " . l:env . " " . l:volumes . " ghcr.io/german-muzquiz/vim-genius:" . s:default_tag . " python -m vim_genius.main"
    "echom l:cmd

    " Create or get output buffer
    let l:output_buf = bufadd(s:genius_output_bufname)

    " Set output buffer options
    call setbufvar(l:output_buf, '&swapfile', 0)
    call setbufvar(l:output_buf, '&filetype', 'genius_output')
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
            \ 'exit_cb': { id, status -> s:on_job_exit(id, status, l:output_buf) },
            \ })

    if job_status(l:job) !=# 'run'
        echom "Failed to start job"
    endif
    " We'll keep the prompt file until the job completes
    " The cleanup will happen in the on_job_exit function
endfunction

" Show history of prompts
function! genius#show_history() abort
    " Create or get history buffer
    let l:history_buf = bufadd(s:genius_history_bufname)
    
    " Set history buffer options
    call setbufvar(l:history_buf, '&swapfile', 0)
    call setbufvar(l:history_buf, '&filetype', 'genius_history')
    call setbufvar(l:history_buf, '&buftype', 'nofile')
    call setbufvar(l:history_buf, '&buflisted', 1)
    
    " Find if history buffer is already displayed in a window
    let l:history_win = bufwinnr(l:history_buf)
    
    if l:history_win == -1
        " History buffer is not displayed, create new split
        silent execute 'edit ' . s:genius_history_bufname
    else
        " History buffer is displayed, switch to its window
        execute l:history_win . 'wincmd w'
    endif
    
    " Switch to the history buffer and clear it
    execute 'buffer' l:history_buf
    
    " Clear and set history buffer content
    silent %delete _
    
    " Get list of history files
    let l:history_files = sort(glob(s:history_dir . '/*.genius', 0, 1), 'N')
    call reverse(l:history_files)
    
    " Add header
    call setline(1, ['# Genius Prompt History', '# Press Enter on a line to load that prompt', ''])
    
    " Add history entries
    for i in range(len(l:history_files))
        let l:file = l:history_files[i]
        let l:filename = fnamemodify(l:file, ':t:r')
        
        " Read the first line of the file
        let l:first_line = ''
        if filereadable(l:file)
            let l:first_line = get(readfile(l:file, '', 1), 0, '')
        endif
        
        call append(line('$'), printf('%d. %s - %s', i+1, l:filename, l:first_line))
    endfor
    
    " Set up mappings for the history buffer
    nnoremap <buffer> <CR> :call <SID>load_history_prompt()<CR>
endfunction

" Load a prompt from history
function! s:load_history_prompt() abort
    " Get the current line
    let l:line = getline('.')
    
    " Extract the index from the line
    let l:index_match = matchlist(l:line, '^\(\d\+\)\.')
    if empty(l:index_match)
        return
    endif
    
    let l:index = str2nr(l:index_match[1]) - 1
    
    " Get list of history files
    let l:history_files = sort(glob(s:history_dir . '/*.genius', 0, 1), 'N')
    call reverse(l:history_files)
    
    if l:index >= 0 && l:index < len(l:history_files)
        " Read the prompt from the file
        let l:prompt = readfile(l:history_files[l:index])
        
        " Open genius buffer and set content
        call genius#open_genius_buffer()
        
        " Clear buffer except header
        if line('$') > len(s:prompt_header)
            execute (len(s:prompt_header) + 1) . ',$delete _'
        endif
        
        " Add prompt content
        call append(line('$'), l:prompt)
        
        " Close history window
        let l:history_win = bufwinnr(s:genius_history_bufname)
        if l:history_win != -1
            execute l:history_win . 'wincmd c'
        endif
    endif
endfunction

" This callback gets called every time new output is received:
function! s:on_job_output(job_id, data, output_buf) abort
    call appendbufline(a:output_buf, '$', a:data)
    redraw
endfunction


" This callback is called when the job finishes.
function! s:on_job_exit(job_id, exit_status, output_buf) abort
    redraw
    echom "Genius finished with status " . a:exit_status
    call s:generate_summary(a:output_buf)
    
    " Clean up the temporary directory
    let l:tmp_dir = fnamemodify(glob('/prompt/prompt.txt'), ':h')
    if !empty(l:tmp_dir) && l:tmp_dir =~ '^/tmp/'
        call delete(l:tmp_dir . '/prompt.txt')
        call delete(l:tmp_dir, 'd')
    endif
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


function! s:generate_summary(output_buf)
    " Find all code blocks and generate a summary
    let l:added = []
    let l:updated = []
    let l:deleted = []
    " Get all lines from the output buffer
    let l:lines = getbufline(a:output_buf, 1, '$')
    let l:total_lines = len(l:lines)
    let l:line_idx = 0
    
    " Iterate through all lines in the buffer
    while l:line_idx < l:total_lines
        let l:line = l:lines[l:line_idx]
        
        " Check if this line contains a code block start
        if l:line =~ '<code_block'
            " Extract filename and operation
            let l:filename = genius#extract_filename_from_tag(l:line)
            let l:operation = genius#extract_operation_from_tag(l:line)
            
            " Add to appropriate list based on operation
            if l:operation == 'add'
                call add(l:added, l:filename)
            elseif l:operation == 'update'
                call add(l:updated, l:filename)
            elseif l:operation == 'delete'
                call add(l:deleted, l:filename)
            endif
            
            " Skip to after the end of this code block
            while l:line_idx < l:total_lines && l:lines[l:line_idx] !~ '</code_block>'
                let l:line_idx += 1
            endwhile
        endif
        
        let l:line_idx += 1
    endwhile

    " Create summary text
    let l:summary = ["--------------------------------------------------------------------------------"]
    call add(l:summary, "File Changes Summary:")
    for l:file in uniq(l:added)
        call add(l:summary, "  " . l:file . " (to add)")
    endfor
    for l:file in uniq(l:updated)
        call add(l:summary, "  " . l:file . " (to update)")
    endfor
    for l:file in uniq(l:deleted)
        call add(l:summary, "  " . l:file . " (to delete)")
    endfor
    call add(l:summary, "--------------------------------------------------------------------------------")
    
    " Append to the end of the buffer
    call appendbufline(a:output_buf, '$', l:summary)
endfunction


" Extract filename from code_block tag
function! genius#extract_filename_from_tag(line) abort
    " Use regex to find the filename attribute in the tag
    let l:match = matchlist(a:line, 'filename="\([^"]*\)"')
    if !empty(l:match)
        return l:match[1]
    endif
    return ''
endfunction

" Extract operation from code_block tag
function! genius#extract_operation_from_tag(line) abort
    " Use regex to find the operation attribute in the tag
    let l:match = matchlist(a:line, 'operation="\([^"]*\)"')
    if !empty(l:match)
        return l:match[1]
    endif
    
    " Default to 'add' if no operation is specified
    return 'add'
endfunction

