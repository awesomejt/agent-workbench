package cmd

import (
	"fmt"
	"os"
	"path/filepath"

	"agent-workbench/cli/internal/render"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Create a repo-level .awb/config.yaml for this project",
	Long: `Write .awb/config.yaml in the current directory so that awb commands
run from this repo automatically target the right project and API.

Example:
  awb init --project my-project
  awb init --project my-project --api-url http://localhost:8000`,
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}
		apiURL := viper.GetString("api_url")
		force, _ := cmd.Flags().GetBool("force")

		configPath := filepath.Join(".awb", "config.yaml")

		if _, err := os.Stat(configPath); err == nil && !force {
			return render.Err("%s already exists; use --force to overwrite", configPath)
		}

		if err := os.MkdirAll(".awb", 0o755); err != nil {
			return render.Err("create .awb directory: %v", err)
		}

		content := fmt.Sprintf("project: %s\napi_url: %s\n", slug, apiURL)
		if err := os.WriteFile(configPath, []byte(content), 0o644); err != nil {
			return render.Err("write config: %v", err)
		}

		render.Line("wrote %s", configPath)
		render.Line("  project: %s", slug)
		render.Line("  api_url: %s", apiURL)
		return nil
	},
}

func init() {
	rootCmd.AddCommand(initCmd)
	initCmd.Flags().Bool("force", false, "Overwrite existing .awb/config.yaml")
}
