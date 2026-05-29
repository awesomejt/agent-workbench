package cmd

import (
	"agent-workbench/cli/internal/api"
	"agent-workbench/cli/internal/render"
	"encoding/json"
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var taskHasWorkCmd = &cobra.Command{
	Use:   "has-work",
	Short: "Exit 0 if the project has available tasks, 1 if not",
	Long: `Check whether the project has any available (pending, unclaimed) tasks.

Exits 0 when at least one task is available to claim, 1 when the queue is empty.
Useful as a shell predicate: awb task has-work && opencode run ...`,
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

		list, err := client.ListTasks(project.ID, api.TaskListOpts{
			Page: 1, PerPage: 1, Available: true,
		})
		if err != nil {
			return render.Err("list tasks: %v", err)
		}

		available := list.Total > 0

		if viper.GetString("output") == "json" {
			type result struct {
				Available bool `json:"available"`
				Count     int  `json:"count"`
			}
			data, _ := json.Marshal(result{Available: available, Count: list.Total})
			fmt.Println(string(data))
		} else if available {
			render.Line("available: yes (%d task(s))", list.Total)
		} else {
			render.Line("available: no")
		}

		if !available {
			os.Exit(1)
		}
		return nil
	},
}

func init() {
	taskCmd.AddCommand(taskHasWorkCmd)
}
