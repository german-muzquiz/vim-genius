" Set up folding for code blocks
setlocal foldmethod=marker
setlocal foldmarker=<code_block,</code_block>
setlocal foldenable
setlocal foldlevel=0

" Make it easier to copy code blocks
nnoremap <buffer> <leader>y :call <SID>yank_code_block()<CR>

" Function to yank the current code block
function! s:yank_code_block()
    " Find the start of the code block
    let l:start = search('<code_block', 'bcnW')
    if l:start == 0
        echo "No code block found"
        return
    endif
    
    " Find the end of the code block
    let l:end = search('</code_block>', 'nW')
    if l:end == 0
        echo "End of code block not found"
        return
    endif
    
    " Yank the content between the markers (excluding the markers)
    let l:start += 1
    let l:end -= 1
    if l:start <= l:end
        execute l:start . ',' . l:end . 'yank'
        echo "Code block yanked"
    endif
endfunction

" Add key mapping to apply diffs
nnoremap <buffer> <leader>a :call <SID>apply_diff()<CR>

" Function to extract filename from code_block tag
function! s:extract_filename_from_tag(line)
    let l:match = matchlist(a:line, 'filename="\([^"]*\)"')
    if !empty(l:match)
        return l:match[1]
    endif
    return ''
endfunction

" Improved function to apply a diff from the output
function! s:apply_diff()
    " Find the start of a diff block
    let l:start = search('<code_block.*operation="update"', 'bcnW')
    if l:start == 0
        echo "No diff block found"
        return
    endif
    
    " Extract filename from the tag
    let l:file = s:extract_filename_from_tag(getline(l:start))
    if empty(l:file)
        echo "Could not find file name for diff"
        return
    endif
    
    " Find the end of the diff block
    let l:end = search('</code_block>', 'nW')
    if l:end == 0
        echo "End of diff block not found"
        return
    endif
    
    " Extract the diff content (excluding the tags)
    let l:diff_content = getline(l:start + 1, l:end - 1)
    
    " Create a temporary file with the diff content
    let l:tmp_diff = tempname()
    call writefile(l:diff_content, l:tmp_diff)
    
    " Check if the target file exists
    if !filereadable(l:file)
        echo "Target file does not exist: " . l:file
        return
    endif
    
    " Apply the diff using the patch command
    let l:cmd = "patch -p0 " . l:file . " < " . l:tmp_diff
    let l:output = system(l:cmd)
    
    " Check if patch was successful
    if v:shell_error
        echo "Failed to apply diff: " . l:output
    else
        echo "Successfully applied diff to " . l:file
        " Reload the file if it's open in a buffer
        let l:buf = bufnr(l:file)
        if l:buf != -1
            execute "buffer " . l:buf . " | edit"
        endif
    endif
endfunction


