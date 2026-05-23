package cmd

import (
	"agent-workbench/cli/internal/render"
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
			return render.Err("resolve project: %v", err)
		}

		statuses, err := client.ListProjectStatus(project.ID)
		if err != nil {
			return render.Err("get status: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(statuses)
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
				render.Str(s.Summary, "-"),
				render.Str(s.Reason, "-"),
				s.UpdatedAt,
			}
		}
		render.Table([]string{"STATUS", "PHASE", "SUMMARY", "REASON", "UPDATED"}, rows)
		return nil
	},
}

func init() {
	rootCmd.AddCommand(statusCmd)
	statusCmd.AddCommand(statusShowCmd)

	statusShowCmd.Flags().String("project", "", "Project slug (overrides --project flag)")
	_ = viper.BindPFlag("project", statusShowCmd.Flags().Lookup("project"))
}
