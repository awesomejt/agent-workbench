package cmd

import (
	"agent-workbench/cli/internal/render"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var taskClaimCmd = &cobra.Command{
	Use:   "claim <task-id>",
	Short: "Claim a task for an agent",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		agentName, err := requireFlag(cmd, "agent")
		if err != nil {
			return err
		}

		duration, _ := cmd.Flags().GetInt("duration")

		client := newClient()
		task, err := client.ClaimTask(args[0], agentName, duration)
		if err != nil {
			return render.Err("claim task: %v", err)
		}

		if viper.GetString("output") == "json" {
			return render.JSON(task)
		}

		render.Line("claimed: %s", task.ID)
		render.Line("agent:   %s", render.Str(task.ClaimedBy, "-"))
		render.Line("until:   %s", render.Str(task.ClaimedUntil, "-"))
		return nil
	},
}

func init() {
	taskCmd.AddCommand(taskClaimCmd)
	taskClaimCmd.Flags().Int("duration", 0, "Lease duration in seconds (0 = use task default)")
}
