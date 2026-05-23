package cmd

import (
	"agent-workbench/cli/internal/api"
	"agent-workbench/cli/internal/render"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var runCmd = &cobra.Command{
	Use:   "run",
	Short: "Manage agent runs",
}

var runStartCmd = &cobra.Command{
	Use:   "start",
	Short: "Start a new run for a project",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}
		agentName, err := requireFlag(cmd, "agent")
		if err != nil {
			return err
		}

		taskID, _ := cmd.Flags().GetString("task")
		summary, _ := cmd.Flags().GetString("summary")

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		run, err := client.CreateRun(project.ID, agentName, taskID, summary)
		if err != nil {
			return render.Err("start run: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(run)
		}
		printRun(run)
		return nil
	},
}

var runGetCmd = &cobra.Command{
	Use:   "get <run-id>",
	Short: "Show details for a run",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		client := newClient()
		run, err := client.GetRun(args[0])
		if err != nil {
			return render.Err("get run: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(run)
		}
		printRun(run)
		return nil
	},
}

var runHeartbeatCmd = &cobra.Command{
	Use:   "heartbeat <run-id>",
	Short: "Send a heartbeat for a running run",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		client := newClient()
		run, err := client.HeartbeatRun(args[0])
		if err != nil {
			return render.Err("heartbeat run: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(run)
		}
		render.Line("heartbeat ok — last_heartbeat_at: %s", render.Str(run.LastHeartbeatAt, "-"))
		return nil
	},
}

var runCompleteCmd = &cobra.Command{
	Use:   "complete <run-id>",
	Short: "Mark a run as completed",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		summary, _ := cmd.Flags().GetString("summary")
		validationResult, _ := cmd.Flags().GetString("validation-result")

		client := newClient()
		run, err := client.CompleteRun(args[0], summary, validationResult)
		if err != nil {
			return render.Err("complete run: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(run)
		}
		render.Line("run %s completed at %s", run.ID[:8], render.Str(run.CompletedAt, "-"))
		return nil
	},
}

var runFailCmd = &cobra.Command{
	Use:   "fail <run-id>",
	Short: "Mark a run as failed",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		summary, _ := cmd.Flags().GetString("summary")

		client := newClient()
		run, err := client.FailRun(args[0], summary)
		if err != nil {
			return render.Err("fail run: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(run)
		}
		render.Line("run %s failed at %s", run.ID[:8], render.Str(run.CompletedAt, "-"))
		return nil
	},
}

func printRun(r api.Run) {
	render.Line("ID:           %s", r.ID)
	render.Line("Status:       %s", r.Status)
	render.Line("Agent:        %s", r.AgentName)
	render.Line("Project:      %s", r.ProjectID)
	if r.TaskID != nil {
		render.Line("Task:         %s", *r.TaskID)
	}
	render.Line("Started:      %s", r.StartedAt)
	render.Line("Heartbeat:    %s", render.Str(r.LastHeartbeatAt, "-"))
	render.Line("Completed:    %s", render.Str(r.CompletedAt, "-"))
	if r.Summary != nil {
		render.Line("Summary:      %s", *r.Summary)
	}
	render.Line("Version:      %d", r.Version)
}

func init() {
	rootCmd.AddCommand(runCmd)
	runCmd.AddCommand(runStartCmd)
	runCmd.AddCommand(runGetCmd)
	runCmd.AddCommand(runHeartbeatCmd)
	runCmd.AddCommand(runCompleteCmd)
	runCmd.AddCommand(runFailCmd)

	runStartCmd.Flags().String("task", "", "Task ID to associate with this run")
	runStartCmd.Flags().String("summary", "", "Initial summary or context")

	runCompleteCmd.Flags().String("summary", "", "Completion summary")
	runCompleteCmd.Flags().String("validation-result", "", "Validation command output")

	runFailCmd.Flags().String("summary", "", "Failure summary or error description")
}
