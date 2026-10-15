# bash completion for inzonectl
_inzonectl() {
  local cur prev
  cur=${COMP_WORDS[COMP_CWORD]}
  prev=${COMP_WORDS[COMP_CWORD-1]}
  if (( COMP_CWORD == 1 )); then
    mapfile -t COMPREPLY < <(compgen -W \
      "status doctor profile game chat mic default volume balance version help" -- "$cur")
  elif [[ ${COMP_WORDS[1]} == doctor && $COMP_CWORD -eq 2 ]]; then
    mapfile -t COMPREPLY < <(compgen -W "--report" -- "$cur")
  elif [[ ${COMP_WORDS[1]} == volume && $COMP_CWORD -eq 2 ]]; then
    mapfile -t COMPREPLY < <(compgen -W "game chat mic" -- "$cur")
  fi
  : "$prev"
}
complete -F _inzonectl inzonectl
