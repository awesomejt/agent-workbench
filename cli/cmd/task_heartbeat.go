package cmd

import (
	"agent-workbench/cli/internal/output"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var taskHeartbeatCmd = &cobra.Command{
	Use:   "heartbeat <task-id>",
	Short: "Extend the lease on a claimed task",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		agentName, err := requireFlag(cmd, "agent")
		if err != nil {
			return err
		}

		client := newClient()
		task, err := client.HeartbeatTask(args[0], agentName)
		if err != nil {
			return output.Err("heartbeat: %v", err)
		}

		if viper.GetString("output") == "json" {
			return output.JSON(task)
		}

		output.Line("heartbeat ok: lease extended until %s", output.Str(task.ClaimedUntil, "-"))
		return nil
	},
}

func init() {
	taskCmd.AddCommand(taskHeartbeatCmd)
}
