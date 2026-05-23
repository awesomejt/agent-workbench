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
		modelID, _ := cmd.Flags().GetString("model")
		promptCategory, _ := cmd.Flags().GetString("prompt-category")
		promptTokens, _ := cmd.Flags().GetInt("prompt-tokens")
		completionTokens, _ := cmd.Flags().GetInt("completion-tokens")
		latencyMs, _ := cmd.Flags().GetInt("latency-ms")

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		metrics := api.RunMetrics{
			ModelID:          modelID,
			PromptCategory:   promptCategory,
			PromptTokens:     promptTokens,
			CompletionTokens: completionTokens,
			LatencyMs:        latencyMs,
		}
		run, err := client.CreateRun(project.ID, agentName, taskID, summary, metrics)
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
		modelID, _ := cmd.Flags().GetString("model")
		promptCategory, _ := cmd.Flags().GetString("prompt-category")
		promptTokens, _ := cmd.Flags().GetInt("prompt-tokens")
		completionTokens, _ := cmd.Flags().GetInt("completion-tokens")
		latencyMs, _ := cmd.Flags().GetInt("latency-ms")

		client := newClient()
		metrics := api.RunMetrics{
			ModelID:          modelID,
			PromptCategory:   promptCategory,
			PromptTokens:     promptTokens,
			CompletionTokens: completionTokens,
			LatencyMs:        latencyMs,
		}
		run, err := client.CompleteRun(args[0], summary, validationResult, metrics)
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
		modelID, _ := cmd.Flags().GetString("model")
		promptCategory, _ := cmd.Flags().GetString("prompt-category")
		promptTokens, _ := cmd.Flags().GetInt("prompt-tokens")
		completionTokens, _ := cmd.Flags().GetInt("completion-tokens")
		latencyMs, _ := cmd.Flags().GetInt("latency-ms")

		client := newClient()
		metrics := api.RunMetrics{
			ModelID:          modelID,
			PromptCategory:   promptCategory,
			PromptTokens:     promptTokens,
			CompletionTokens: completionTokens,
			LatencyMs:        latencyMs,
		}
		run, err := client.FailRun(args[0], summary, metrics)
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
	if r.ModelID != nil {
		render.Line("Model:        %s", *r.ModelID)
	}
	if r.PromptCategory != nil {
		render.Line("Category:     %s", *r.PromptCategory)
	}
	if r.PromptTokens != nil {
		out := 0
		if r.CompletionTokens != nil {
			out = *r.CompletionTokens
		}
		render.Line("Tokens:       in=%d out=%d", *r.PromptTokens, out)
	}
	if r.LatencyMs != nil {
		render.Line("Latency:      %dms", *r.LatencyMs)
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
	runStartCmd.Flags().String("model", "", "Model ID used for this run (e.g. claude-sonnet-4-6)")
	runStartCmd.Flags().String("prompt-category", "", "Prompt category (e.g. code, research, review)")
	runStartCmd.Flags().Int("prompt-tokens", 0, "Input token count")
	runStartCmd.Flags().Int("completion-tokens", 0, "Output token count")
	runStartCmd.Flags().Int("latency-ms", 0, "Total latency in milliseconds")

	runCompleteCmd.Flags().String("summary", "", "Completion summary")
	runCompleteCmd.Flags().String("validation-result", "", "Validation command output")
	runCompleteCmd.Flags().String("model", "", "Model ID used for this run")
	runCompleteCmd.Flags().String("prompt-category", "", "Prompt category")
	runCompleteCmd.Flags().Int("prompt-tokens", 0, "Input token count")
	runCompleteCmd.Flags().Int("completion-tokens", 0, "Output token count")
	runCompleteCmd.Flags().Int("latency-ms", 0, "Total latency in milliseconds")

	runFailCmd.Flags().String("summary", "", "Failure summary or error description")
	runFailCmd.Flags().String("model", "", "Model ID used for this run")
	runFailCmd.Flags().String("prompt-category", "", "Prompt category")
	runFailCmd.Flags().Int("prompt-tokens", 0, "Input token count")
	runFailCmd.Flags().Int("completion-tokens", 0, "Output token count")
	runFailCmd.Flags().Int("latency-ms", 0, "Total latency in milliseconds")
}
