package cmd

import (
	"agent-workbench/cli/internal/output"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var projectCmd = &cobra.Command{
	Use:   "project",
	Short: "Manage projects",
}

var projectListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all projects",
	RunE: func(cmd *cobra.Command, args []string) error {
		client := newClient()
		list, err := client.ListProjects(1, 100)
		if err != nil {
			return output.Err("list projects: %v", err)
		}

		if viper.GetString("output") == "json" {
			return output.JSON(list)
		}

		if len(list.Items) == 0 {
			fmt.Println("no projects found")
			return nil
		}

		rows := make([][]string, len(list.Items))
		for i, p := range list.Items {
			rows[i] = []string{
				p.Slug,
				p.Name,
				p.ProjectType,
				p.Environment,
				output.Str(p.LocalPath, "-"),
			}
		}
		output.Table([]string{"SLUG", "NAME", "TYPE", "ENV", "LOCAL PATH"}, rows)
		return nil
	},
}

func init() {
	rootCmd.AddCommand(projectCmd)
	projectCmd.AddCommand(projectListCmd)
}
