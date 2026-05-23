package cmd

import (
	"agent-workbench/cli/internal/api"
	"agent-workbench/cli/internal/render"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "View and manage project status",
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
				s.ID[:8],
				s.Status,
				s.Phase,
				render.Str(s.Summary, "-"),
				render.Str(s.Reason, "-"),
				s.UpdatedAt,
			}
		}
		render.Table([]string{"ID", "STATUS", "PHASE", "SUMMARY", "REASON", "UPDATED"}, rows)
		return nil
	},
}

var statusCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new status record for a project",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}
		status, _ := cmd.Flags().GetString("status")
		phase, _ := cmd.Flags().GetString("phase")
		if status == "" || phase == "" {
			return render.Err("--status and --phase are required")
		}

		body := map[string]any{"status": status, "phase": phase}
		if v, _ := cmd.Flags().GetString("summary"); v != "" {
			body["summary"] = v
		}
		if v, _ := cmd.Flags().GetString("reason"); v != "" {
			body["reason"] = v
		}
		if v, _ := cmd.Flags().GetString("source"); v != "" {
			body["source"] = v
		}

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		rec, err := client.CreateStatus(project.ID, body)
		if err != nil {
			return render.Err("create status: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(rec)
		}
		printStatus(rec)
		return nil
	},
}

var statusUpdateCmd = &cobra.Command{
	Use:   "update <status-id>",
	Short: "Update an existing status record",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}
		version, _ := cmd.Flags().GetInt("version")
		if version == 0 {
			return render.Err("--version is required")
		}

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		body := map[string]any{"version": version}
		if v, _ := cmd.Flags().GetString("status"); v != "" {
			body["status"] = v
		}
		if v, _ := cmd.Flags().GetString("phase"); v != "" {
			body["phase"] = v
		}
		if v, _ := cmd.Flags().GetString("summary"); v != "" {
			body["summary"] = v
		}
		if v, _ := cmd.Flags().GetString("reason"); v != "" {
			body["reason"] = v
		}

		rec, err := client.UpdateStatus(project.ID, args[0], body)
		if err != nil {
			return render.Err("update status: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(rec)
		}
		printStatus(rec)
		return nil
	},
}

func printStatus(s api.ProjectStatus) {
	render.Line("ID:      %s", s.ID)
	render.Line("Status:  %s", s.Status)
	render.Line("Phase:   %s", s.Phase)
	render.Line("Summary: %s", render.Str(s.Summary, "-"))
	render.Line("Reason:  %s", render.Str(s.Reason, "-"))
	render.Line("Version: %d", s.Version)
	render.Line("Updated: %s", s.UpdatedAt)
}

func init() {
	rootCmd.AddCommand(statusCmd)
	statusCmd.AddCommand(statusShowCmd)
	statusCmd.AddCommand(statusCreateCmd)
	statusCmd.AddCommand(statusUpdateCmd)

	statusShowCmd.Flags().String("project", "", "Project slug (overrides --project flag)")
	_ = viper.BindPFlag("project", statusShowCmd.Flags().Lookup("project"))

	statusCreateCmd.Flags().String("status", "", "Status value (required)")
	statusCreateCmd.Flags().String("phase", "", "Phase (required)")
	statusCreateCmd.Flags().String("summary", "", "Status summary")
	statusCreateCmd.Flags().String("reason", "", "Reason for the status change")
	statusCreateCmd.Flags().String("source", "", "Source of the status update (default: cli)")

	statusUpdateCmd.Flags().Int("version", 0, "Current version (required for optimistic locking)")
	statusUpdateCmd.Flags().String("status", "", "New status value")
	statusUpdateCmd.Flags().String("phase", "", "New phase")
	statusUpdateCmd.Flags().String("summary", "", "New summary")
	statusUpdateCmd.Flags().String("reason", "", "New reason")
}
