<script setup lang="ts">
import Button from 'primevue/button';
import Toolbar from "primevue/toolbar";
import {invoke} from '@tauri-apps/api/tauri';

const greeting = ref("");
const cards = ref([]);

onMounted(() => {
  invoke<string>('greet', {name: 'Next.js'})
      .then((result) => {
        greeting.value = result;
      })
      .catch(console.error)

  for (let i = 0; i < 30; i++) {
    cards.value.push({
      filename: "file-" + i,
      type: "a"
    })
  }
})

</script>

<template>
  <div class="bg-cyan-950 h-dvh">
    <div class="h-svh">
      <!-- Search Bar -->
      <div class="p-3 bg-cyan-900 h-1/6 max-h-25">
        <Toolbar>
          <template #start>
            <Button icon="pi pi-plus" class="mr-2"/>
            <Button icon="pi pi-print" class="mr-2"/>
            <Button icon="pi pi-upload"/>
          </template>

          <template #center>
            <span class="relative">
              <i class="pi pi-search absolute top-2/4 -mt-2 left-3 text-surface-400 dark:text-surface-600"/>
              <InputText placeholder="Search" class="pl-10"/>
            </span>
          </template>

          <template #end>
            <!--              <SplitButton label="Save" icon="pi pi-check" :model="items"></SplitButton>-->
          </template>
        </Toolbar>
      </div>
      <!-- Bottom Part -->

      <div class="h-5/6">
        <div class="flex h-full">
          <div class="p-3 w-3/4">
            <ScrollPanel class="h-full">
              <div class="flex flex-wrap gap-4">
                <Card v-for="item in cards" class="w-48 h-48">
                  <template #title>{{item.filename}}</template>
                  <template #content>{{item.type}}</template>
                </Card>
              </div>
            </ScrollPanel>


            <!--        <Splitter style="height: 300px">-->
            <!--          <SplitterPanel class="flex items-center justify-center" :size="75"> Panel 1 </SplitterPanel>-->
            <!--          <SplitterPanel class="flex items-center justify-center" :size="25" :minSize="10"> Panel 2 </SplitterPanel>-->
            <!--        </Splitter>-->
          </div>
          <!-- Tiles -->
          <Divider layout="vertical"></Divider>
          <div class="w-1/4">
            <Card>
              <<template #title> Simple Card </template>
              <template #content>
                <p class="m-0">
                  Lorem ipsum
                </p>
              </template>
            </Card>
          </div>
        </div>
      </div>

    </div>
  </div>


</template>

