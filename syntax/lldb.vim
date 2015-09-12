syn match LLCmdMarker /→/ conceal contained
syn match LLCmd /→.*$/ contains=LLCmdMarker
syn match LLCmdOutMarker /✓/ conceal contained
syn match LLCmdOut /✓.*$/ contains=LLCmdOutMarker
syn match LLCmdErrMarker /✗/ conceal contained
syn match LLCmdErr /✗.*$/ contains=LLCmdErrMarker

hi def link LLCmdMarker Ignore
hi def link LLCmdOutMarker Ignore
hi def link LLCmdErrMarker Ignore

hi def link LLCmd Comment
hi def link LLCmdOut Debug
hi def link LLCmdErr Exception
