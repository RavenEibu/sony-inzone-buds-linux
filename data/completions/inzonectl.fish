# fish completion for inzonectl
complete -c inzonectl -f
complete -c inzonectl -n __fish_use_subcommand -a 'status doctor profile game chat mic default volume balance version help'
complete -c inzonectl -n '__fish_seen_subcommand_from doctor' -a '--report'
complete -c inzonectl -n '__fish_seen_subcommand_from volume' -a 'game chat mic'
