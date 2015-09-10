syn match LLDebugSym /✓/ conceal contained
syn match LLDebugLine /✓.*$/ contains=LLDebugSym
syn match LLDebugErrSym /✗/ conceal contained
syn match LLDebugErrLine /✗.*$/ contains=LLDebugErrSym

hi def link LLDebugSym Ignore
hi def link LLDebugErrSym Ignore
hi def link LLDebugLine Debug
hi def link LLDebugErrLine Exception
