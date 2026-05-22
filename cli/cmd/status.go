package cmd

import (
	"agent-workbench/cli/internal/output"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "View project status",
}

var statusShowCmd = &cobra.Command{
	Use:   "show",
	Short: "Show the current status of a project",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return output.Err("resolve project: %v", err)
		}

		statuses, err := client.ListProjectStatus(project.ID)
		if err != nil {
			return output.Err("get status: %v", err)
		}

		if viper.GetString("output") == "json" {
			return output.JSON(statuses)
		}

		if len(statuses.Items) == 0 {
			fmt.Printf("no status records for project %q\n", slug)
			return nil
		}

		rows := make([][]string, len(statuses.Items))
		for i, s := range statuses.Items {
			rows[i] = []string{
				s.Status,
				s.Phase,
				output.Str(s.Summary, "-"),
				output.Str(s.Reason, "-"),
				s.UpdatedAt,
			}
		}
		output.Table([]string{"STATUS", "PHASE", "SUMMARY", "REASON", "UPDATED"}, rows)
		return nil
	},
}

func init() {
	rootCmd.AddCommand(statusCmd)
	statusCmd.AddCommand(statusShowCmd)

	statusShowCmd.Flags().String("project", "", "Project slug (overrides --project flag)")
	_ = viper.BindPFlag("project", statusShowCmd.Flags().Lookup("project"))
}
