package cmd

import (
	"agent-workbench/cli/internal/render"
	"os"

	"github.com/spf13/cobra"
)

var completionCmd = &cobra.Command{
	Use:       "completion [bash|zsh|fish|powershell]",
	Short:     "Generate shell completion script",
	ValidArgs: []string{"bash", "zsh", "fish", "powershell"},
	Args:      cobra.ExactArgs(1),
	Long: `Generate a shell completion script for awb and print it to stdout.

Source the script in your shell profile to enable tab completion:

  bash:
    awb completion bash > /etc/bash_completion.d/awb
    # or: source <(awb completion bash)

  zsh:
    awb completion zsh > "${fpath[1]}/_awb"
    # or: source <(awb completion zsh)

  fish:
    awb completion fish > ~/.config/fish/completions/awb.fish

  powershell:
    awb completion powershell | Out-String | Invoke-Expression
`,
	RunE: func(cmd *cobra.Command, args []string) error {
		switch args[0] {
		case "bash":
			return rootCmd.GenBashCompletion(os.Stdout)
		case "zsh":
			return rootCmd.GenZshCompletion(os.Stdout)
		case "fish":
			return rootCmd.GenFishCompletion(os.Stdout, true)
		case "powershell":
			return rootCmd.GenPowerShellCompletion(os.Stdout)
		default:
			return render.Err("unsupported shell %q — use bash, zsh, fish, or powershell", args[0])
		}
	},
}

func init() {
	rootCmd.AddCommand(completionCmd)
}
