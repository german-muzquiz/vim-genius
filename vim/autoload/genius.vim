
" Constants
let s:default_tag = 'latest'
let s:genius_home = expand('~/.genius')
let s:genius_config_file = s:genius_home . '/config.env'
let s:genius_prompt_file = s:genius_home . '/current_chat.genius'
let s:genius_log_file = s:genius_home . '/genius.log'
let s:genius_staging_folder = s:genius_home . '/staging'
let s:genius_history_folder = s:genius_home . '/history'
let s:genius_bufname = 'Genius'
let s:genius_tree_bufname = 'Genius: Diff'
let s:genius_history_bufname = 'Genius: History'
let s:max_history_files = 20
let s:is_processing = 0
let s:animation_frames = ['-', '\', '|', '/']
let s:animation_line_number = 1

" Buffer options
let s:buffer_options = {
    \ 'buflisted': 1,
    \ 'buftype': 'nofile',
    \ 'swapfile': 0,
    \ 'filetype': 'genius',
    \ 'wrap': 0,
    \ 'cursorline': 1,
    \ 'number': 1,
    \ }

" Prompt header
let s:prompt_header = [
    \ '---------------------------------------------------------------------------------',
    \ 'Help',
    \ '<Enter> - Sends the current prompt to the LLM',
    \ '<leader>h - Show prompt history',
    \ '<leader>c - Opens the Genius configuration file',
    \ '',
    \ 'Inject files and folders:',
    \ '@folder/ - Injects the contents of the folder into the prompt',
    \ '@file - Injects the contents of the file into the prompt',
    \ '@https://abc.com - Injects the contents of the URL into the prompt',
    \ '',
    \ 'Type @ and press Tab to autocomplete file paths',
    \ '---------------------------------------------------------------------------------',
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
        call mkdir(s:genius_history_folder, "p", 0700)
        call writefile(l:default_config, s:genius_config_file)
    endif
    
    " Open config file in a new buffer
    execute 'edit ' . s:genius_config_file
    
    " Set buffer options
    setlocal filetype=sh
endfunction


" Create and setup the genius chat
function! genius#open_genius_chat(new_chat=0) abort
    let l:is_new_file = 0
    if a:new_chat || !filereadable(s:genius_prompt_file)
        " Create a new file for the prompt
        call writefile(s:prompt_header, s:genius_prompt_file)
        let l:is_new_file = 1
    endif

    " Check if buffer is already loaded
    let l:buf = s:get_buf_nr(s:genius_bufname)
    let l:is_new_buf = l:buf == -1
    if l:buf == -1
        let l:buf = bufadd(s:genius_bufname)
        " Set buffer options
        for [key, value] in items(s:buffer_options)
            call setbufvar(l:buf, '&' . key, value)
        endfor
    endif

    " Switch to the buffer
    execute 'buffer' l:buf

    " Load the contents of the genius prompt file into the buffer
    if l:is_new_buf
        call setbufline(l:buf, 1, readfile(s:genius_prompt_file))
        if l:is_new_file
            normal G
        endif
    endif

    " Set up autocompletion
    setlocal completefunc=s:complete_filepath

    " Set buffer-local keymap
    nnoremap <buffer> <Enter> :call <SID>execute_buffer()<CR>
    nnoremap <buffer> <leader>h :call genius#show_history()<CR>
    nnoremap <buffer> <leader>c :call genius#open_config()<CR>
    nnoremap <buffer> <leader>d :call <SID>show_staging_tree()<CR>

    " Save buffer contents when it is unloaded
    augroup GeniusLoaded
        autocmd!
        autocmd BufUnload * call s:save_genius_buffer()
    augroup end
endfunction


" Save genius buffer
function! s:save_genius_buffer() abort
    if bufname('%') == s:genius_bufname
        call writefile(getline(1, '$'), s:genius_prompt_file)
    endif
endfunction


" Return the number of the buffer with the given exact name, or -1 if not found
function! s:get_buf_nr(name)
    for buf in getbufinfo()
        if buf.name == a:name
            return buf.bufnr
        endif
    endfor
    return -1
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
function! s:save_to_history() abort
    if !filereadable(s:genius_prompt_file)
        return
    endif

    " Create timestamp for filename
    let l:timestamp = strftime('%Y%m%d_%H%M%S')
    let l:filename = s:genius_history_folder . '/' . l:timestamp . '.genius'

    " Create foler if it doesn't exist
    call mkdir(s:genius_history_folder, "p", 0700)
    
    " Write current prompt to file
    call writefile(readfile(s:genius_prompt_file), l:filename)
    
    " Clean up old history files if we have too many
    let l:history_files = sort(glob(s:genius_history_folder . '/*.genius', 0, 1))
    if len(l:history_files) > s:max_history_files
        call delete(l:history_files[0])
    endif
    return l:filename
endfunction

" Execute the buffer content using the LLM
function! s:execute_buffer() abort
    " Save buffer contents to chat prompt file
    call writefile(getline(1, '$'), s:genius_prompt_file)

    " Save chat to history
    call s:save_to_history()

    " Empty the staging folder
    call delete(s:genius_staging_folder, 'rf')
    call mkdir(s:genius_staging_folder, "p", 0700)

    let l:volumes = s:get_volumes_to_mount()
    let l:env = s:get_env_vars_to_mount()
    let l:cmd = "/bin/sh -c \"docker run --rm " . l:env . " " . l:volumes . " ghcr.io/german-muzquiz/vim-genius:" . s:default_tag . " python -m vim_genius.main"
    "echom l:cmd

    " Create or get output buffer
    let l:output_buf = bufadd(s:genius_bufname)

    " Find if output buffer is already displayed in a window
    let l:output_win = bufwinnr(l:output_buf)
    
    if l:output_win == -1
        " Output buffer is not displayed, open it
        silent execute 'edit ' . s:genius_bufname
    else
        " Output buffer is displayed, switch to its window
        execute l:output_win . 'wincmd w'
    endif
    
    " Switch to the output buffer and clear it
    let l:current_win = winnr() 
    execute 'buffer' l:output_buf
    call appendbufline(l:output_buf, '$', ['', '', ''])

    " Set processing flag
    let s:is_processing = 1
    let s:animation_line_number = line('$')
    let s:animation_timer = timer_start(100, function('s:update_animation'), {'repeat': -1})

    " Start the asynchronous job
    let l:job = job_start(l:cmd, {
            \ 'out_cb': { id, data -> s:on_job_output(id, data, l:output_buf) },
            \ 'err_cb': { id, data -> s:on_job_output(id, data, l:output_buf) },
            \ 'exit_cb': { id, status -> s:on_job_exit(id, status, l:output_buf) },
            \ })

    if job_status(l:job) !=# 'run'
        echom "Failed to start job"
    endif
endfunction

" Get the volumes to be mounted into the container as a string to be passed to
" the docker run command
function! s:get_volumes_to_mount() abort
    let l:volumes = ' -v ' . s:genius_home . ':/root/.genius' " Genius home
    let l:volumes = l:volumes . ' -v $PWD:/workspace' " Current working directory
    " Add AWS config folder only if API_FAMILY is bedrock
    if filereadable(s:genius_config_file) && system('grep "^API_FAMILY=bedrock" ' . s:genius_config_file) != ''
        let l:volumes = l:volumes . '-v $HOME/.aws:/root/.aws'
    endif
    return l:volumes
endfunction


" Get the env vars to be passed to the container as a string to be passed to
" the docker run command
function! s:get_env_vars_to_mount() abort
    let l:env = ''
    " Add AWS env vars only if API_FAMILY is bedrock
    if filereadable(s:genius_config_file) && system('grep "^API_FAMILY=bedrock" ' . s:genius_config_file) != ''
        let l:env = l:env . ' -e AWS_PROFILE -e AWS_REGION -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN'
    endif
    return l:env
endfunction


" Function to update the animation in the output buffer
function! s:update_animation(timer) abort
    let l:output_buf = bufnr(s:genius_bufname)
    if l:output_buf == -1
        return
    endif
    
    if !s:is_processing
        call timer_stop(a:timer)
        call setbufline(l:output_buf, s:animation_line_number, '')
        return
    endif
    
    " Get the current frame and update the index
    let s:current_frame = get(s:, 'current_frame', 0)
    let s:current_frame = (s:current_frame + 1) % len(s:animation_frames)
    
    " Update the first line of the buffer with the animation
    let l:animation_text = '==> Thinking ' . s:animation_frames[s:current_frame]
    call setbufline(l:output_buf, s:animation_line_number, l:animation_text)
    
    redraw
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
    let l:history_files = sort(glob(s:genius_history_folder . '/*.genius', 0, 1), 'N')
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
    nnoremap <buffer> <CR> :call <SID>load_chat_history()<CR>
endfunction

" Load a chat from history
function! s:load_chat_history() abort
    " Get the current line
    let l:line = getline('.')
    
    " Extract the index from the line
    let l:index_match = matchlist(l:line, '^\(\d\+\)\.')
    if empty(l:index_match)
        return
    endif
    
    let l:index = str2nr(l:index_match[1]) - 1
    
    " Get list of history files
    let l:history_files = sort(glob(s:genius_history_folder . '/*.genius', 0, 1), 'N')
    call reverse(l:history_files)
    
    if l:index >= 0 && l:index < len(l:history_files)
        " Copy the chat to the genius_prompt_file
        call writefile(readfile(l:history_files[l:index]), s:genius_prompt_file)
        
        " Open genius buffer and set content
        call genius#open_genius_chat()
        
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
    let s:is_processing = 0
    echom "Genius finished with status " . a:exit_status
    call s:generate_summary(a:output_buf)
endfunction


" Helper function to trigger completion after inserting a directory
function! s:trigger_completion_after_dir() abort
    call feedkeys("\<C-x>\<C-u>", 'n')
endfunction


" File path completion function
function! s:complete_filepath(findstart, base) abort
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
    let l:summary = ["---------------------------------------------------------------------------------"]
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
    call add(l:summary, "---------------------------------------------------------------------------------")
    
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


" Function to extract code blocks from the output buffer
function! s:extract_code_blocks() abort
    let l:output_buf = bufnr(s:genius_bufname)
    if l:output_buf == -1
        echo "Output buffer not found"
        return {}
    endif
    
    let l:lines = getbufline(l:output_buf, 1, '$')
    let l:total_lines = len(l:lines)
    let l:line_idx = 0
    let l:code_blocks = {}
    
    " Iterate through all lines in the buffer
    while l:line_idx < l:total_lines
        let l:line = l:lines[l:line_idx]
        
        " Check if this line contains a code block start
        if l:line =~ '<code_block'
            " Extract filename, operation, and filetype
            let l:filename = genius#extract_filename_from_tag(l:line)
            let l:operation = genius#extract_operation_from_tag(l:line)
            let l:filetype = matchlist(l:line, 'filetype="\([^"]*\)"')[1]
            
            " Start collecting content
            let l:content = []
            let l:line_idx += 1
            
            " Collect content until the end of the code block
            while l:line_idx < l:total_lines && l:lines[l:line_idx] !~ '</code_block>'
                call add(l:content, l:lines[l:line_idx])
                let l:line_idx += 1
            endwhile
            
            " Store the code block
            let l:code_blocks[l:filename] = {
                \ 'operation': l:operation,
                \ 'filetype': l:filetype,
                \ 'content': l:content
                \ }
        endif
        
        let l:line_idx += 1
    endwhile
    
    return l:code_blocks
endfunction

" Show the tree view of files in the staging folder
function! s:show_staging_tree() abort
    " Create or get tree buffer
    let l:tree_buf = bufadd(s:genius_tree_bufname)
    
    " Set tree buffer options
    call setbufvar(l:tree_buf, '&swapfile', 0)
    call setbufvar(l:tree_buf, '&filetype', 'genius_diff')
    call setbufvar(l:tree_buf, '&buftype', 'nofile')
    call setbufvar(l:tree_buf, '&buflisted', 1)
    
    " Find if tree buffer is already displayed in a window
    let l:tree_win = bufwinnr(l:tree_buf)
    
    if l:tree_win == -1
        execute 'vertical leftabove 40split | buffer' l:tree_buf
    else
        " Tree buffer is displayed, switch to its window
        execute l:tree_win . 'wincmd w'
    endif
    
    " Clear and set tree buffer content
    silent %delete _
    
    " Add header
    call setline(1, ['File Changes:'])
    
    " Check if staging folder exists
    if !isdirectory(s:genius_staging_folder)
        call append(line('$'), ['', 'No files in staging area.'])
        return
    endif
    
    " Get list of files in staging folder
    let l:files = glob(s:genius_staging_folder . '/**/*', 0, 1)
    let l:added_files = []
    let l:updated_files = []
    let l:deleted_files = []
    
    for l:file in l:files
        if l:file =~ '\.patch$'
            continue
        elseif l:file =~ '\.delete$'
            let l:file = substitute(l:file, s:genius_staging_folder . '/', '', '')
            let l:file = substitute(l:file, '\.delete$', '', '')
            call add(l:deleted_files, l:file)
        elseif filereadable(l:file)
            " Check if this is a new or updated file
            let l:rel_path = substitute(l:file, s:genius_staging_folder . '/', '', '')
            if filereadable(getcwd() . '/' . l:rel_path)
                call add(l:updated_files, l:rel_path)
            else
                call add(l:added_files, l:rel_path)
            endif
        endif
    endfor
    
    " Add files to the buffer with appropriate prefixes
    call append(line('$'), [''] + map(l:added_files, '"+ " . v:val') + map(l:updated_files, '"~ " . v:val') + map(l:deleted_files, '"- " . v:val'))
    
    " Set up mappings for the tree buffer
    nnoremap <buffer> <CR> :call <SID>show_file_diff()<CR>
    nnoremap <buffer> <Esc> :bdelete! <bar> :bdelete! <bar> :bdelete!<CR>
endfunction

" Function to show diff between proposed file and current file
function! s:show_file_diff() abort
    " Get the current line
    let l:line = getline('.')
    
    " Skip if this is a header or empty line
    if l:line =~ '^File Changes:' || l:line =~ '^\s*$'
        return
    endif
    
    " Extract the filename from the line
    let l:match = matchlist(l:line, '[+~-] \(.*\)')
    if empty(l:match)
        echo "Could not extract filename from line"
        return
    endif
    
    let l:filename = l:match[1]
    
    " Determine operation type from the line prefix
    let l:operation = ''
    if l:line =~ '^\s*+'
        let l:operation = 'add'
    elseif l:line =~ '^\s*\~'
        let l:operation = 'update'
    elseif l:line =~ '^\s*-'
        let l:operation = 'delete'
    else
        echo "Could not determine operation type from line"
        return
    endif

    " Original is relative to pwd
    let l:original = getcwd() . '/' . l:filename
    let l:new = s:genius_staging_folder . '/' . l:filename

    " Open the original and new files in a vertical split to the right of the file tree
    " with the original file on the left and the new file on the right, in diff mode
    " First maximize the tree pane
    execute 'wincmd o'
    " Open the original file in a vertical split
    execute 'vertical rightbelow split ' . l:original
    execute 'diffthis'
    " Resize tree pane to 40 columns
    execute 'wincmd h'
    execute 'vertical resize 40'
    " Open new file in a vertical split
    execute 'wincmd l'
    execute 'vertical rightbelow split ' . l:new
    execute 'diffthis'
    execute 'wincmd h | wincmd h'
    
endfunction

