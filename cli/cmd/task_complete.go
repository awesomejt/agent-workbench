package cmd

import (
	"agent-workbench/cli/internal/render"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var taskCompleteCmd = &cobra.Command{
	Use:   "complete <task-id>",
	Short: "Mark a task as completed",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		agentName, err := requireFlag(cmd, "agent")
		if err != nil {
			return err
		}
		evidence, _ := cmd.Flags().GetString("evidence")

		client := newClient()
		task, err := client.CompleteTask(args[0], agentName, evidence, newIdempotencyKey())
		if err != nil {
			return render.Err("complete task: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(task)
		}

		render.Line("completed: %s (version %d)", task.ID, task.Version)
		return nil
	},
}

func init() {
	taskCmd.AddCommand(taskCompleteCmd)
	taskCompleteCmd.Flags().String("evidence", "", "Completion evidence or summary")
}
