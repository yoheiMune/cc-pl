<template>
  <div class="main">

    <h1>Annual report for CoinCheck</h1>

    <md-card>
      <md-card-header>
        <div class="md-title">Enter your information.</div>
      </md-card-header>
      <md-card-content>
        <md-subheader>Step1: Select the year.</md-subheader>
        <md-field>
          <md-select v-model="year">
            <md-option value="2017">2017</md-option>
          </md-select>
        </md-field>

        <md-subheader>Step2: Upload your activities.</md-subheader>
        <md-field>
          <label>Trade (Optional)</label>
          <md-file v-model="trading" />
        </md-field>
        <md-field>
          <label>Buy (Optional)</label>
          <md-file v-model="buying" />
        </md-field>
        <md-field>
          <label>Sell (Optional)</label>
          <md-file v-model="selling" />
        </md-field>
        <md-field>
          <label>Send (Optional)</label>
          <md-file v-model="sending" />
        </md-field>

        <md-button class="md-primary">Create a report</md-button>
      </md-card-content>
    </md-card>

  <md-card class="result">
    <md-card-header>
      <div class="md-title">Report</div>
    </md-card-header>
    <md-card-content>
      <p>Input your information first.</p>
    </md-card-content>

  </md-card>



  </div>
</template>

<script>
export default {
  name: 'HelloWorld',
  data () {
    return {
      year: '2017',
      trading: null,
      buying: null,
      selling: null,
      sending: null
    }
  }
}
</script>

<style scoped>
h1, h2 {
  font-weight: normal;
}
h1 {
  margin-bottom: 48px;
}
.main {
  max-width: 900px;
  margin-left: auto;
  margin-right: auto;
  padding: 16px;
}
.md-field {
  margin-left: 16px;
  margin-right: 16px;
  width: calc(100% - 32px);
}
.result {
  margin-top: 48px;
}
</style>
