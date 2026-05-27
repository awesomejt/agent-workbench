package cmd

import (
	"agent-workbench/cli/internal/render"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var taskCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new task in a project",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}

		title, _ := cmd.Flags().GetString("title")
		if title == "" {
			return render.Err("--title is required")
		}

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		body := map[string]any{"title": title}

		if v, _ := cmd.Flags().GetString("description"); v != "" {
			body["description"] = v
		}
		if v, _ := cmd.Flags().GetString("phase"); v != "" {
			body["phase"] = v
		}
		if v, _ := cmd.Flags().GetInt("priority"); cmd.Flags().Changed("priority") {
			body["priority"] = v
		}
		if v, _ := cmd.Flags().GetString("status"); v != "" {
			body["status"] = v
		}
		if v, _ := cmd.Flags().GetString("role"); v != "" {
			body["role"] = v
		}
		if v, _ := cmd.Flags().GetString("model-tier"); v != "" {
			body["model_tier"] = v
		}
		if v, _ := cmd.Flags().GetString("section"); v != "" {
			body["project_section_id"] = v
		}
		if v, _ := cmd.Flags().GetInt("duration"); cmd.Flags().Changed("duration") {
			body["estimated_duration_seconds"] = v
		}
		if v, _ := cmd.Flags().GetString("validation"); v != "" {
			body["validation_expectations"] = v
		}

		task, err := client.CreateTask(project.ID, body)
		if err != nil {
			return render.Err("create task: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(task)
		}

		render.Line("created: %s", task.ID)
		render.Line("title:   %s", task.Title)
		render.Line("status:  %s", task.Status)
		render.Line("phase:   %s", task.Phase)
		render.Line("priority: %d", task.Priority)
		return nil
	},
}

func init() {
	taskCmd.AddCommand(taskCreateCmd)
	taskCreateCmd.Flags().String("title", "", "Task title (required)")
	taskCreateCmd.Flags().String("description", "", "Task description")
	taskCreateCmd.Flags().String("phase", "", "Phase: discovery, design, implementation, testing, review")
	taskCreateCmd.Flags().Int("priority", 0, "Priority (higher = more urgent)")
	taskCreateCmd.Flags().String("status", "", "Initial status: new (triage queue) or pending (ready to claim). Default: pending")
	taskCreateCmd.Flags().String("role", "", "Role: researcher, planner, implementer, writer, reviewer, tester, orchestrator")
	taskCreateCmd.Flags().String("model-tier", "", "Model tier: local or cloud")
	taskCreateCmd.Flags().String("section", "", "Project section UUID")
	taskCreateCmd.Flags().Int("duration", 0, "Estimated duration in seconds")
	taskCreateCmd.Flags().String("validation", "", "Validation expectations")
}
