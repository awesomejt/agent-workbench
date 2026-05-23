package cmd

import (
	"agent-workbench/cli/internal/render"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var taskBlockCmd = &cobra.Command{
	Use:   "block <task-id>",
	Short: "Mark a task as blocked",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		agentName, err := requireFlag(cmd, "agent")
		if err != nil {
			return err
		}
		reason, _ := cmd.Flags().GetString("reason")

		client := newClient()
		task, err := client.BlockTask(args[0], agentName, reason, newIdempotencyKey())
		if err != nil {
			return render.Err("block task: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(task)
		}

		render.Line("blocked: %s", task.ID)
		if reason != "" {
			render.Line("reason:  %s", reason)
		}
		return nil
	},
}

func init() {
	taskCmd.AddCommand(taskBlockCmd)
	taskBlockCmd.Flags().String("reason", "", "Reason the task is blocked")
}
