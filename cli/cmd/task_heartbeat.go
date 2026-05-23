package cmd

import (
	"agent-workbench/cli/internal/render"

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
		task, err := client.HeartbeatTask(args[0], agentName, newIdempotencyKey())
		if err != nil {
			return render.Err("heartbeat: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(task)
		}

		render.Line("heartbeat ok: lease extended until %s", render.Str(task.ClaimedUntil, "-"))
		return nil
	},
}

func init() {
	taskCmd.AddCommand(taskHeartbeatCmd)
}
