package cmd

import (
	"agent-workbench/cli/internal/api"
	"agent-workbench/cli/internal/output"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var taskCmd = &cobra.Command{
	Use:   "task",
	Short: "Manage tasks",
}

var taskListCmd = &cobra.Command{
	Use:   "list",
	Short: "List tasks for a project",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}
		statusFilter, _ := cmd.Flags().GetString("status")
		phaseFilter, _ := cmd.Flags().GetString("phase")

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return output.Err("resolve project: %v", err)
		}

		list, err := client.ListTasks(project.ID, api.TaskListOpts{
			Page: 1, PerPage: 50,
			Status: statusFilter,
			Phase:  phaseFilter,
		})
		if err != nil {
			return output.Err("list tasks: %v", err)
		}

		if viper.GetString("output") == "json" {
			return output.JSON(list)
		}

		if len(list.Items) == 0 {
			fmt.Println("no tasks found")
			return nil
		}

		rows := make([][]string, len(list.Items))
		for i, t := range list.Items {
			rows[i] = []string{
				t.ID[:8],
				t.Status,
				fmt.Sprintf("%d", t.Priority),
				t.Phase,
				output.Str(t.ClaimedBy, "-"),
				t.Title,
			}
		}
		output.Table([]string{"ID", "STATUS", "PRI", "PHASE", "CLAIMED BY", "TITLE"}, rows)
		output.Line("\n%d task(s) — page %d of %d", list.Total, list.Page, list.Pages)
		return nil
	},
}

var taskGetCmd = &cobra.Command{
	Use:   "get <task-id>",
	Short: "Show details for a task",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		client := newClient()
		task, err := client.GetTask(args[0])
		if err != nil {
			return output.Err("get task: %v", err)
		}

		if viper.GetString("output") == "json" {
			return output.JSON(task)
		}

		printTask(task)
		return nil
	},
}

var taskNextCmd = &cobra.Command{
	Use:   "next",
	Short: "Show the highest-priority pending task for a project",
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return output.Err("resolve project: %v", err)
		}

		list, err := client.ListTasks(project.ID, api.TaskListOpts{
			Page: 1, PerPage: 1, Status: "pending",
		})
		if err != nil {
			return output.Err("list tasks: %v", err)
		}

		if len(list.Items) == 0 {
			fmt.Println("no pending tasks")
			return nil
		}

		if viper.GetString("output") == "json" {
			return output.JSON(list.Items[0])
		}

		printTask(list.Items[0])
		return nil
	},
}

// printTask writes a human-readable task detail block.
func printTask(t api.Task) {
	output.Line("ID:          %s", t.ID)
	output.Line("Title:       %s", t.Title)
	output.Line("Status:      %s", t.Status)
	output.Line("Priority:    %d", t.Priority)
	output.Line("Phase:       %s", t.Phase)
	output.Line("Claimed by:  %s", output.Str(t.ClaimedBy, "-"))
	output.Line("Claimed until: %s", output.Str(t.ClaimedUntil, "-"))
	if t.EstimatedDurationSeconds != nil {
		output.Line("Est. duration: %ds", *t.EstimatedDurationSeconds)
	}
	if t.Description != nil {
		output.Line("Description: %s", *t.Description)
	}
	if t.CompletionEvidence != nil {
		output.Line("Evidence:    %s", *t.CompletionEvidence)
	}
	output.Line("Version:     %d", t.Version)
	output.Line("Updated:     %s", t.UpdatedAt)
}

func init() {
	rootCmd.AddCommand(taskCmd)
	taskCmd.AddCommand(taskListCmd)
	taskCmd.AddCommand(taskGetCmd)
	taskCmd.AddCommand(taskNextCmd)

	taskListCmd.Flags().String("status", "", "Filter by status (pending, completed, blocked)")
	taskListCmd.Flags().String("phase", "", "Filter by phase")
}
