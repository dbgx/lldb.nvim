let name = expand('%')[6:]
if name == 'logs'
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
elseif name == 'backtrace'
  syn match LLFrameNumber /frame \zs#[0-9]\+/ contained
  syn match LLSelectedFrame /^  \* .*/ contains=LLFrameNumber
  syn match LLOtherFrame /^    .*/ contains=LLFrameNumber

  hi def link LLFrameNumber Number
  hi def link LLSelectedFrame Statement
  hi def link LLOtherFrame Comment
elseif name == 'breakpoints'
  syn match LLBpId /^[0-9]\+/ contained
  syn match LLBpParams /[a-z]\+ = \zs[^,]\+\|resolved/ contained
  syn match LLBpLine /^[0-9]\+: .*/ contains=LLBpId,LLBpParams
  syn match LLBpLocLine /^  [0-9]\+.[0-9]\+: .*/ contains=LLBpParams

  hi def link LLBpId Number
  hi def link LLBpParams Identifier
  hi def link LLBpLine Statement
  hi def link LLBpLocLine Comment
elseif name == 'locals'
  syn match LLVarType /^(\zs.\+\ze)/ contained
  syn match LLVarIdent /) \zs\i\+\ze = /
  syn match LLVarLine /^([^=]\+\i\+ = .*/ contains=LLVarType,LLVarIdent

  hi def link LLVarType Type
  hi def link LLVarIdent Identifier
elseif name == 'threads'
  syn match LLThreadNumber /thread \zs#[0-9]\+/ contained
  syn match LLThreadParams /[:,] [a-z ]\+ = \zs[^,]\+/ contained
  syn match LLSelectedThread /^\* .*/ contains=LLThreadNumber,LLThreadParams
  syn match LLOtherThread /^  .*/ contains=LLThreadNumber,LLThreadParams

  hi def link LLThreadNumber Number
  hi def link LLThreadParams Identifier
  hi def link LLSelectedThread Statement
  hi def link LLOtherThread Comment
elseif name == 'registers'
  syn match LLRegHex /0x[0-9a-f]\+/
  syn match LLRegIdent /^ \+\zs\i\+\ze = /
  syn cluster LLRegLine contains=LLRegIdent,LLRegIdent

  hi def link LLRegHex Number
  hi def link LLRegIdent Identifier
elseif name == 'disassembly'
  set syntax=asm
endif

"¹ 1S
"² 2S
"✠ -X
"‡ /=
"※ :X
"→ ->
"⇒ =>
"✗ XX
"✓ OK
"♀ Fm
